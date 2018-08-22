from collections import OrderedDict

from urllib.parse import urlencode

import requests

from django.conf import settings

from elections.models import Election as YNRElection
from popolo.models import Post, Organization
from candidates.models import (
    PostExtra,
    OrganizationExtra,
    PartySet,
    PostExtraElection,
)


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
        org_name = self["organisation"]["official_name"]
        classification = self["organisation"]["organisation_type"]
        org_slug = ":".join([classification, self["organisation"]["slug"]])

        if hasattr(self, "organization_object"):
            self.organization_created = False
        else:
            try:
                organization_extra = OrganizationExtra.objects.get(
                    slug=org_slug, base__classification=classification
                )
                organization = organization_extra.base
                self.organization_created = False
            except OrganizationExtra.DoesNotExist:
                organization = Organization.objects.create(
                    name=org_name, classification=classification
                )
                organization_extra = OrganizationExtra.objects.create(
                    base=organization, slug=org_slug
                )
                self.organization_created = True

            self.organization_object = organization
        return (self.organization_object, self.organization_created)

    def get_or_create_election(self):
        if hasattr(self, "election_object"):
            self.election_created = False
        else:
            party_lists_in_use = False
            if self["voting_system"]:
                party_lists_in_use = self["voting_system"]["uses_party_lists"]

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
                },
            )
            self.election_object = election_obj
            self.election_created = created
        return (self.election_object, self.election_created)

    def get_or_create_partyset(self):
        """
        The list of parties used for this election depends on the territory.
        Currently only Northern Ireland uses a different set.
        """
        # TODO Pass in party sets to save queries for each post

        # The division can have a different code to the organisation
        # for example UK wide orgs like `parl` has divisions in 4 differet
        # territories. We need to use the most specific code here.
        if hasattr(self, "party_set_object"):
            self.party_set_created = False
        else:
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

            self.party_set_object, self.party_set_created = PartySet.objects.update_or_create(
                slug=country, defaults={"name": partyset_name}
            )
        return (self.party_set_object, self.party_set_created)

    def get_or_create_post(self):
        if not self.parent or self.children:
            raise ValueError("Can't create YNR Post from a election group ID")

        if hasattr(self, "post_object"):
            self.post_created = False
        else:
            # Make an organisation
            self.get_or_create_organisation()

            if self["division"]:
                # Case 1, there is an organisational division relted to this
                # post
                slug = ":".join(
                    [
                        self["division"]["division_type"],
                        self["division"]["geography_curie"].split(":")[-1],
                    ]
                )
                label = self["division"]["name"]
                role = self["division"]["geography_curie"]
            else:
                # Case 2, this organisation isn't split in to divisions for
                # this election, take the info from the organisation directly
                slug = self["organisation"]["slug"]
                label = self["organisation"]["official_name"]
                role = self["elected_role"]
            try:
                post_extra = PostExtra.objects.get(slug=slug)
                self.post_object = post_extra.base
                self.post_created = False
            except PostExtra.DoesNotExist:
                self.post_object = Post.objects.create(
                    label=label, organization=self.organization_object
                )
                post_extra = PostExtra.objects.create(
                    base=self.post_object, slug=slug
                )
                self.post_created = True

            self.post_object.role = role
            self.post_object.label = label
            self.post_object.organization = self.organization_object
            self.post_object.save()
            post_extra.party_set = self.get_or_create_partyset()[0]
            post_extra.save()
        return (self.post_object, self.post_created)

    def get_or_create_post_election(self, parent):
        if hasattr(self, "post_extra_object"):
            self.post_extra_created = False
        else:
            # First, set up the Post and Election with related objects
            self.get_or_create_post()

            # Make sure we're creating an ID for the right parent
            assert self.parent == parent["election_id"], "{} != {}".format(
                self.parent, parent["election_id"]
            )

            # Note that we create the election of the parent
            parent.get_or_create_election()

            # Get the winner count
            winner_count = self["seats_contested"]

            self.post_extra_object, self.post_extra_created = PostExtraElection.objects.update_or_create(
                postextra=self.post_object.extra,
                election=parent.election_object,
                defaults={
                    "ballot_paper_id": self["election_id"],
                    "winner_count": winner_count,
                },
            )
        return (self.post_extra_object, self.post_extra_created)


def is_mayor_or_pcc_ballot(election):
    return election.is_leaf_node and election["election_type"][
        "election_type"
    ] in ["mayor", "pcc"]


class EveryElectionImporter(object):
    def __init__(self, query_args=None):
        self.EE_BASE_URL = getattr(
            settings, "EE_BASE_URL", "https://elections.democracyclub.org.uk/"
        )

        self.election_tree = {}
        if not query_args:
            query_args = {"current": "True"}
        self.query_args = query_args

    def build_election_tree(self):
        """
        Get all current elections from Every Election and build them in to
        a tree of IDs
        """

        url = "{}api/elections/".format(self.EE_BASE_URL)
        prams = urlencode(OrderedDict(sorted(self.query_args.items())))
        url = "{}?{}".format(url, prams)
        while url:
            req = requests.get(url)
            req.raise_for_status()
            data = req.json()
            for result in data["results"]:
                election_id = result["election_id"]
                self.election_tree[election_id] = EEElection(result)
            url = data.get("next")

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
        return ballots

    def get_parent(self, election_id):
        child = self.election_tree[election_id]
        return self.election_tree[child.parent]
