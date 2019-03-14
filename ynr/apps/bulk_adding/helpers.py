import json
import csv

from parties.models import Party, PartyDescription
from popolo.models import Membership
from people.models import Person

from bulk_adding.models import RawPeople

from candidates.models import LoggedAction, raise_if_unsafe_to_delete
from candidates.models.auth import check_creation_allowed
from candidates.views.version_data import get_change_metadata, get_client_ip


def add_person(request, person_data):
    person = Person.objects.create(name=person_data["name"])

    change_metadata = get_change_metadata(request, person_data["source"])

    person.record_version(change_metadata, new_person=True)
    person.save()

    LoggedAction.objects.create(
        user=request.user,
        person=person,
        action_type="person-create",
        ip_address=get_client_ip(request),
        popit_person_new_version=change_metadata["version_id"],
        source=change_metadata["information_source"],
    )
    return person


def update_person(
    request=None, person=None, party=None, post_election=None, source=None
):
    election = post_election.election

    person.not_standing.remove(election)

    check_creation_allowed(request.user, person.current_candidacies)

    membership, _ = Membership.objects.update_or_create(
        post=post_election.post,
        person=person,
        role=election.candidate_membership_role,
        post_election=post_election,
        defaults={"party": party, "party_list_position": None, "elected": None},
    )

    # Now remove other memberships in this election for that
    # person, although we raise an exception if there is any
    # object that has a
    # ForeignKey to the membership, since that would result in
    # losing data.
    old_memberships = Membership.objects.exclude(pk=membership.pk).filter(
        person=person,
        post_election=post_election,
        role=election.candidate_membership_role,
    )
    for old_membership in old_memberships:
        raise_if_unsafe_to_delete(old_membership)
        old_membership.delete()

    change_metadata = get_change_metadata(request, source)

    person.record_version(change_metadata)
    person.save()

    LoggedAction.objects.create(
        user=request.user,
        person=person,
        action_type="person-update",
        ip_address=get_client_ip(request),
        popit_person_new_version=change_metadata["version_id"],
        source=change_metadata["information_source"],
    )


class CSVImporter:
    def __init__(self, file_name, election):
        self.csv_data = list(csv.DictReader(open(file_name).readlines()))
        self.header_rows = self.csv_data[0].keys()
        self.election = election

        self.validate_posts()

        self.ballots = {}
        for ballot in self.election.postextraelection_set.all():
            self.ballots[ballot.ballot_paper_id] = {
                "ballot": ballot,
                "data": [],
            }

    @property
    def post_header_name(self):
        POST_LABELS = ["Electoral Area Name", "Election Area"]
        for label in POST_LABELS:
            if label in self.header_rows:
                return label

    @property
    def party_description_header_name(self):
        DESCRIPTION_FIELDS = ["Description", "Candidates Description"]
        for description_field in DESCRIPTION_FIELDS:
            if description_field in self.header_rows:
                return description_field

    def match_division_to_ballot(self, row):
        post_name = row[self.post_header_name]
        for ballot in self.election.postextraelection_set.all():
            if ballot.post.label == post_name:
                return ballot

    def format_name(self, row):
        FULL_NAME_FIELDS = ["Ballot Paper Name"]
        for name_field in FULL_NAME_FIELDS:
            if name_field in self.header_rows:
                return row[name_field]

        name = []

        FIRST_NAME_FIELDS = ["Forename"]
        LAST_NAME_FIELDS = ["Surname"]

        for name_part in [FIRST_NAME_FIELDS, LAST_NAME_FIELDS]:
            for name_field in name_part:
                if name_field in self.header_rows:
                    name.append(row[name_field])

        return " ".join(name)

    def get_party_description(self, row):
        desc = row[self.party_description_header_name]

        try:
            return PartyDescription.objects.get(description=desc)
        except PartyDescription.DoesNotExist:
            try:
                return PartyDescription.objects.get(
                    description__startswith="{} |".format(desc)
                )
            except:
                return None

    def get_party_id(self, row, ballot_model):
        desc_model = self.get_party_description(row)
        if desc_model:
            return desc_model.party.ec_id

        if row[self.party_description_header_name] in ("", None):
            return "ynmp-party:2"
        print(repr(row[self.party_description_header_name]))

        group = ballot_model.post.group
        if group == "Northern Ireland":
            register = "ni"
        else:
            register = "gb"
        return (
            Party.objects.register(register)
            .get(name=row[self.party_description_header_name])
            .ec_id
        )
        # return self._get_party_description(row).party.ec_id

    def validate_posts(self):
        """
        Figure out if the posts in this CSV look right, raise if not
        """

        unique_posts = set(
            [row[self.post_header_name] for row in self.csv_data]
        )
        if len(unique_posts) != self.election.postextraelection_set.count():
            raise ValueError("Number of posts don't match")

        return True

    def extract(self):
        for row in self.csv_data:
            ballot_model = self.match_division_to_ballot(row)
            ballot_dict = self.ballots[ballot_model.ballot_paper_id]
            print(self.format_name(row))
            print(self.get_party_id(row, ballot_model))
            data = {
                "name": self.format_name(row),
                "party_id": self.get_party_id(row, ballot_model),
            }
            desc = self.get_party_description(row)
            if desc:
                data["description_id"] = desc.pk
            ballot_dict["data"].append(data)

        for ballot_id, ballot_dict in self.ballots.items():
            RawPeople.objects.update_or_create(
                ballot=ballot_dict["ballot"],
                defaults={
                    "data": json.dumps(ballot_dict["data"]),
                    "source": "CSV from Council",
                    "source_type": RawPeople.SOURCE_COUNCIL_CSV,
                },
            )
