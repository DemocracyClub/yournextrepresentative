from collections import OrderedDict
from datetime import date, timedelta
from time import sleep
from urllib.parse import urlencode, urljoin

import requests
from candidates.models import Ballot, PartySet
from django.conf import settings
from django.utils.dateparse import parse_datetime
from elections.models import Election as YNRElection
from popolo.models import Organization, Post

ALWAYS_USES_LISTS = ["europarl"]

ELECTION_CACHE = {}
POST_CACHE = {}
ORGANISATION_CACHE = {}
PARTYSET_CACHE = {}


class EEElection(dict):
    """
    An "Election" object represents something stored by EveryElection.

    It knows how to turn itself in to a Post or Election in YNR terms
    depending on the type of election group it is. This is a slight fudge
    as YNR only has 2 tiers of "election"; the group (or "Election") and the
    post object. EE has up to 4 tiers down to the ballot paper ID.
    """

    @property
    def parent(self):
        return self["group"]

    @property
    def children(self):
        return self["children"]

    @property
    def is_leaf_node(self):
        return not self["children"] and self["group_type"] in [
            "organisation",
            None,
        ]

    def get_or_create_organisation(self):
        if not self["organisation"]:
            return (None, False)
        org_name = self["organisation"]["official_name"]
        classification = self["organisation"]["organisation_type"]
        org_slug = ":".join([classification, self["organisation"]["slug"]])

        if hasattr(self, "organization_object"):
            self.organization_created = False
        else:
            try:
                organization = Organization.objects.get(
                    slug=org_slug, classification=classification
                )
                self.organization_created = False
            except Organization.DoesNotExist:
                organization = Organization.objects.create(
                    name=org_name, classification=classification, slug=org_slug
                )
                self.organization_created = True

            self.organization_object = organization
        return (self.organization_object, self.organization_created)

    def get_or_create_election(self):
        if self["election_id"] in ELECTION_CACHE:
            self.election_created = False
            self.election_object = ELECTION_CACHE[self["election_id"]]
        else:
            party_lists_in_use = self._set_party_lists_in_use()

            election_obj, created = YNRElection.objects.update_or_create(
                slug=self["election_id"],
                election_date=self["poll_open_date"],
                defaults={
                    "current": self["current"],
                    "candidate_membership_role": "Candidate",
                    "for_post_role": self["election_type"]["name"],
                    "show_official_documents": True,
                    "name": self["election_title"],
                    "party_lists_in_use": party_lists_in_use,
                    "organization": self.get_or_create_organisation()[0],
                    "ee_modified": self.get("modified"),
                },
            )
            self.election_object = election_obj
            self.election_created = created
            ELECTION_CACHE[self["election_id"]] = election_obj
        return (self.election_object, self.election_created)

    def _set_party_lists_in_use(self):
        election_type = self["election_id"].split(".")[0]
        if election_type in ALWAYS_USES_LISTS:
            return True

        if self["voting_system"]:
            return self["voting_system"]["uses_party_lists"]

        return False

    def get_or_create_partyset(self):
        """
        The list of parties used for this election depends on the territory.
        Currently only Northern Ireland uses a different set.
        """
        # The division can have a different code to the organisation
        # for example UK wide orgs like `parl` has divisions in 4 differet
        # territories. We need to use the most specific code here.
        if self["division"] and self["division"]["territory_code"]:
            territory_code = self["division"]["territory_code"]
        else:
            territory_code = self["organisation"]["territory_code"]

        if territory_code == "NIR":
            partyset_name = "Northern Ireland"
            country = "ni"
        else:
            partyset_name = "Great Britain"
            country = "gb"

        if country in PARTYSET_CACHE:
            self.party_set_created = False
            self.party_set_object = PARTYSET_CACHE[country]
        else:
            (
                self.party_set_object,
                self.party_set_created,
            ) = PartySet.objects.update_or_create(
                slug=country, defaults={"name": partyset_name}
            )
            PARTYSET_CACHE[country] = self.party_set_object
        return (self.party_set_object, self.party_set_created)

    def get_or_create_post(self):
        """
        Get or create a post based on the division and division set
        from EveryElection

        This is compex for a number of reasons:

        1. Sometimes we have elections for organisations that don't have
           sub-divisions. We need to make a post in that case anyway, so we use
           information about the organisation to emulate a post here.

        2. Some divisions have IDs that change over time, mainly because they
           don't have GSS codes when we first see them. We need to detect this
           case and update the IDs accordingly.

        3. When we are able to retrieve an existing Post object with the slug,
           org and start date provided, we check if it has been updated since
           the last import by comparing the ee_modified timestamp we have
           stored. If nothing has changed, it gets added to the cache and the
           updated is skipped - this is to stop the Post.modified field from
           updating when no values have changed. This is necessary because when
           WCIVF importer checks for Ballot updates in YNR, the related post
           modified timestamp is checked (see last_updated method on the
           BallotQueryset).
        """

        if not self.parent or self.children:
            raise ValueError("Can't create YNR Post from a election group ID")

        # Make an organisation
        org, created = self.get_or_create_organisation()
        if self["division"]:
            # Case 1, there is an organisational division related to this
            # post
            slug = self["division"]["slug"]
            label = self["division"]["name"]
            role = self["division"]["official_identifier"]
            identifier = self["division"]["official_identifier"]
            start_date = self["division"]["divisionset"]["start_date"]
            end_date = self["division"]["divisionset"]["end_date"]
            territory_code = self["division"]["territory_code"]
            ee_modified = self["division"].get("modified", "")
        else:
            # Case 2, this organisation isn't split in to divisions for
            # this election, take the info from the organisation directly
            slug = self["organisation"]["slug"]
            label = self["organisation"]["official_name"]
            role = self["elected_role"]
            identifier = self["organisation"]["official_identifier"]
            start_date = self["organisation"]["start_date"]
            end_date = self["organisation"]["end_date"]
            territory_code = self["organisation"]["territory_code"]
            ee_modified = self["organisation"].get("modified", "")

        # check the cache first, return early if possible
        cache_key = "--".join([slug, self.organization_object.slug, start_date])
        if cache_key in POST_CACHE:
            self.post_created = False
            self.post_object = POST_CACHE[cache_key]
            return (self.post_object, self.post_created)

        # try to find an existing object
        try:
            self.post_object = Post.objects.get(
                slug=slug,
                organization=self.organization_object,
                start_date=start_date,
            )
            self.post_created = False
        except Post.DoesNotExist:
            self.post_object = Post(
                organization=self.organization_object,
                slug=slug,
                start_date=start_date,
                identifier=identifier,
            )
            self.post_created = True

        # if it wasnt created and nothing has changed we can return
        # early and skip updating the object in our DB
        ee_modified = parse_datetime(ee_modified)
        if (
            ee_modified
            and not self.post_created
            and self.post_object.ee_modified
            and self.post_object.ee_modified >= ee_modified
        ):
            # add to the cache
            POST_CACHE[cache_key] = self.post_object
            return self.post_object, self.post_created

        self.post_object.role = role
        self.post_object.label = label
        self.post_object.party_set = self.get_or_create_partyset()[0]
        self.post_object.organization = self.organization_object

        old_identifier = self.post_object.identifier

        self.post_object.identifier = identifier
        self.post_object.territory_code = territory_code
        self.post_object.end_date = end_date
        self.post_object.ee_modified = ee_modified
        self.post_object.save()

        if old_identifier != identifier:
            self.post_object.postidentifier_set.create(
                label="dc_slug", identifier=old_identifier
            )

        POST_CACHE[cache_key] = self.post_object
        return (self.post_object, self.post_created)

    def get_replaced_ballot(self):
        replaces = self.get("replaces")
        if not replaces:
            return None
        try:
            return Ballot.objects.get(ballot_paper_id=replaces)
        except Ballot.DoesNotExist:
            return None

    def get_or_create_ballot(self, parent):
        """
        Parent may be None if this is a recently-updated import. In
        this case it indicates that the parent has not been modified
        in EE so we can skip the get_or_creat_election step
        """
        if hasattr(self, "ballot_object"):
            return self.ballot_object, False
        # First, set up the Post and Election with related objects
        self.get_or_create_post()

        voting_system = self["voting_system"] or {}
        ballot_data = {
            "post": self.post_object,
            "winner_count": self["seats_contested"] or 1,
            "cancelled": self["cancelled"],
            "replaces": self.get_replaced_ballot(),
            "tags": self.get("tags", {}),
            "by_election_reason": self.get("by_election_reason", ""),
            "voting_system": voting_system.get("slug", ""),
            "ee_modified": self.get("modified"),
        }
        if ballot_data["cancelled"]:
            ballot_data["candidates_locked"] = True

        # if we have a parent Election update it then add it to
        # the dict to be used to update the Ballot
        if parent:
            assert self.parent == parent["election_id"], "{} != {}".format(
                self.parent, parent["election_id"]
            )
            # Note that we create the election of the parent
            parent.get_or_create_election()
            ballot_data["election"] = parent.election_object

        (
            self.ballot_object,
            self.ballot_created,
        ) = Ballot.objects.update_or_create(
            ballot_paper_id=self["election_id"], defaults=ballot_data
        )

        return (self.ballot_object, self.ballot_created)

    def delete_ballot(self):
        try:
            ballot = Ballot.objects.get(ballot_paper_id=self["election_id"])
        except Ballot.DoesNotExist:
            # if it doesn't already exist, this might be because:
            # - we deleted it in EE before it was ever imported into YNR
            # - we already deleted it
            # either way, we wanted it gone and now its not there
            return

        try:
            ballot.safe_delete()
        except Ballot.UnsafeToDelete as e:
            raise type(e)(str(e) + ". Manual review needed")

    def delete_election(self):
        try:
            election = YNRElection.objects.get(slug=self["election_id"])
        except YNRElection.DoesNotExist:
            # if it doesn't already exist, job done
            # - we deleted it in EE before it was ever imported into YNR
            # - we already deleted it
            # - this EE group type doesn't map to an election in YNR
            # either way, we wanted it gone and now its not there
            return

        try:
            election.safe_delete()
        except YNRElection.UnsafeToDelete as e:
            raise type(e)(str(e) + ". Manual review needed")


def is_mayor_or_pcc_ballot(election):
    return election.is_leaf_node and election["election_type"][
        "election_type"
    ] in ["mayor", "pcc"]


class EveryElectionImporter(object):
    def __init__(self, query_args=None, election_id=None):
        self.election_id = election_id
        self.EE_BASE_URL = getattr(
            settings, "EE_BASE_URL", "https://elections.democracyclub.org.uk/"
        )
        self.url = urljoin(self.EE_BASE_URL, "/api/elections/")

        self.election_tree: dict[str:EEElection] = {}
        if query_args is None:
            query_args = {
                "poll_open_date__gte": str(date.today() - timedelta(days=30))
            }
        # never import referendums
        # NB if this requirement changes, should add election types as an
        # option to uk_create_elections_fromn_every_election management command
        query_args["exclude_election_id_regex"] = r"^ref\..*"
        self.query_args = query_args

    def count_results(self) -> int:
        """
        Return the count for a given set of filters
        """

        url = self.build_url_with_query_args()
        req = requests.get(url)
        req.raise_for_status()
        return int(req.json().get("count", 0))

    def build_url_with_query_args(self):
        params = urlencode(OrderedDict(sorted(self.query_args.items())))
        return f"{self.url}?{params}"

    def url_to_election_tree(self, url: str, counter: int = 0):
        while url:
            req = requests.get(url)
            req.raise_for_status()
            data = req.json()
            total = data["count"]

            for result in data["results"]:
                election_id = result["election_id"]
                self.election_tree[election_id] = EEElection(result)
                counter += 1
            if counter:
                print(f"Added {counter} of {total}")
            url = data.get("next")
        return self.election_tree

    def build_election_tree(self, deleted=False) -> dict:
        """
        Get all current elections from Every Election and build them in to
        a tree of IDs
        """

        if self.election_id:
            url = f"{self.url}{self.election_id}"
            req = requests.get(url)
            req.raise_for_status()
            data = req.json()
            election_id = data["election_id"]
            self.election_tree[election_id] = EEElection(data)
            return self.election_tree

        if "modified" in self.query_args:
            url = self.build_url_with_query_args()
            return self.url_to_election_tree(url)

        # First pass: just get elections
        self.query_args["identifier_type"] = "election"
        url = self.build_url_with_query_args()
        print(url)
        print("Importing elections")
        self.url_to_election_tree(url)

        # Second pass: get the children
        print("Importing ballots")
        for election_id, election in self.election_tree.copy().items():
            if not settings.RUNNING_TESTS:
                sleep(1)
            for child in election["children"]:
                parts = child.split(".")
                date = parts.pop(-1)
                parent_prefix = ".".join(parts[:2])
                url = urljoin(
                    self.EE_BASE_URL,
                    f"api/elections/?poll_open_date={date}&election_id_regex={parent_prefix}",
                )
                if deleted:
                    url = f"{url}&deleted=1"
                self.url_to_election_tree(url)
        return self.election_tree

    @property
    def ballot_ids(self):
        ballots = {}
        for k, v in self.election_tree.items():
            if v["group_type"] is None:
                ballots[k] = v
            if is_mayor_or_pcc_ballot(v):
                ballots[k] = v
                # note: this (intentionally) creates a circular reference
                # we need to be careful how we parse this data structure
                ballots[k]["group"] = v["election_id"]
            if v["election_id"][:-10] == "gla.a.":
                ballots[k] = v
                ballots[k]["group"] = v["election_id"]

        return ballots

    @property
    def group_ids(self):
        groups = {}
        for k, v in self.election_tree.items():
            if v["group_type"] in ["election", "organisation"]:
                groups[k] = v
            if v["election_id"][:-10] == "gla.a.":
                groups[k] = v
        return groups

    def get_parent(self, election_id):
        child = self.election_tree[election_id]
        if election_id[:-10] == "gla.a.":
            return child

        if child.parent not in self.election_tree:
            new_importer = EveryElectionImporter(election_id=child.parent)
            new_importer.build_election_tree()
            self.election_tree.update(new_importer.election_tree)

        return self.election_tree[child.parent]

    def get_children(self, election_id):
        parent = self.election_tree[election_id]
        children = []

        for child_id in parent["children"]:
            if child_id not in self.election_tree:
                new_importer = EveryElectionImporter(election_id=child_id)
                new_importer.build_election_tree()
                self.election_tree.update(new_importer.election_tree)
            self.election_tree[child_id]
            children.append(self.election_tree[child_id])

        return children
