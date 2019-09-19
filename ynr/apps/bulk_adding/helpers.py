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
    request=None,
    person=None,
    party=None,
    ballot=None,
    source=None,
    list_position=None,
):
    election = ballot.election

    person.not_standing.remove(election)

    check_creation_allowed(request.user, person.current_or_future_candidacies)

    membership, _ = Membership.objects.update_or_create(
        post=ballot.post,
        person=person,
        ballot=ballot,
        defaults={
            "party": party,
            "party_list_position": list_position,
            "elected": None,
            "role": election.candidate_membership_role,
        },
    )

    # Now remove other memberships in this election for that
    # person, although we raise an exception if there is any
    # object that has a
    # ForeignKey to the membership, since that would result in
    # losing data.
    old_memberships = (
        Membership.objects.exclude(pk=membership.pk)
        .exclude(ballot__candidates_locked=True)
        .filter(person=person, ballot__election=ballot.election)
    )
    for old_membership in old_memberships:
        raise_if_unsafe_to_delete(old_membership)
        old_membership.delete()

    memberships_for_election = Membership.objects.filter(
        person=person, ballot__election=ballot.election
    )

    if (
        not memberships_for_election.exists()
        or memberships_for_election.count() > 1
    ):
        raise ValueError(
            "Attempt to create invalid memberships for {}".format(person)
        )

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
        for ballot in self.election.ballot_set.all():
            self.ballots[ballot.ballot_paper_id] = {
                "ballot": ballot,
                "data": [],
            }

    @property
    def post_header_name(self):
        POST_LABELS = [
            "Electoral Area Name",
            "Election Area",
            "AreaName",
            "AREA_NAME",
        ]
        for label in POST_LABELS:
            if label in self.header_rows:
                return label
        raise ValueError("No post header matched")

    @property
    def party_description_header_name(self):
        DESCRIPTION_FIELDS = [
            "Description",
            "Candidates Description",
            "CandidateDescription",
            "CandidateLine5",
            "PARTY_OFFICIAL",
        ]
        for description_field in DESCRIPTION_FIELDS:
            if description_field in self.header_rows:
                return description_field
        raise ValueError("No party description header matched")

    def clean_area_name(self, name):

        name = name.replace(" Ward", "").strip().lower()
        name = name.replace("`", "'")
        name = name.replace(" & ", " and ")
        return name

    def match_division_to_ballot(self, row):
        post_name = self.clean_area_name(row[self.post_header_name])
        for ballot in self.election.ballot_set.all():
            print(self.clean_area_name(ballot.post.label), post_name)
            if self.clean_area_name(ballot.post.label) == post_name:
                return ballot
        raise ValueError("No ballot matched to {}".format(post_name))

    def format_name(self, row):
        FULL_NAME_FIELDS = ["Ballot Paper Name"]
        for name_field in FULL_NAME_FIELDS:
            if name_field in self.header_rows:
                return row[name_field]

        name = []

        FIRST_NAME_FIELDS = [
            "Forename",
            "CandidateForename",
            "CandidateLine2",
            "CAND_CFOR",
        ]
        LAST_NAME_FIELDS = [
            "Surname",
            "CandidateSurname",
            "CandidateLine1",
            "CAND_CSUR_CAPS",
        ]

        for name_part in [FIRST_NAME_FIELDS, LAST_NAME_FIELDS]:
            for name_field in name_part:
                if name_field in self.header_rows:
                    name_part = row[name_field]
                    if name_part.upper() == name_part:
                        # This is all upper case, title case it
                        name_part = name_part.title()
                    name.append(name_part)
        if name:
            return " ".join(name)

        raise ValueError("Blank name")

    def get_register_for_ballot(self, ballot):
        group = ballot.post.group
        if group == "Northern Ireland":
            register = "NI"
        else:
            register = "GB"
        return register

    def clean_party_name(self, name):
        if name == "Ukip":
            name = "UKIP"
        return name

    def get_party_description(self, row, ballot):
        register = self.get_register_for_ballot(ballot)
        desc = self.clean_party_name(row[self.party_description_header_name])
        try:
            return PartyDescription.objects.get(
                description=desc, party__register=register
            )
        except PartyDescription.DoesNotExist:
            try:
                return PartyDescription.objects.get(
                    description__startswith="{} |".format(desc),
                    party__register=register,
                )
            except PartyDescription.DoesNotExist:
                return None

    def get_party_id(self, row, ballot_model):
        register = self.get_register_for_ballot(ballot_model)
        desc_model = self.get_party_description(row, ballot_model)
        if desc_model:
            return desc_model.party.ec_id

        party_name = self.clean_party_name(
            row[self.party_description_header_name]
        )

        if party_name in ("", None):
            return "ynmp-party:2"
        print(repr(party_name))

        return Party.objects.register(register).get(name=party_name).ec_id

    def validate_posts(self):
        """
        Figure out if the posts in this CSV look right, raise if not
        """

        unique_posts = set(
            [row[self.post_header_name] for row in self.csv_data]
        )
        if len(unique_posts) != self.election.ballot_set.count():
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
            desc = self.get_party_description(row, ballot_model)
            if desc:
                data["description_id"] = str(desc.pk)
            ballot_dict["data"].append(data)

        for ballot_id, ballot_dict in self.ballots.items():
            RawPeople.objects.update_or_create(
                ballot=ballot_dict["ballot"],
                defaults={
                    "data": ballot_dict["data"],
                    "source": "CSV from Council",
                    "source_type": RawPeople.SOURCE_COUNCIL_CSV,
                },
            )
