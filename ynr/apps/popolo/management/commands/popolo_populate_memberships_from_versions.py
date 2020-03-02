import json

from django.core.management.base import BaseCommand
from django.db import transaction

from candidates.models import Ballot
from parties.models import Party
from people.models import Person
from popolo.models import Membership


class Command(BaseCommand):
    help = """
    A command for looking at person versions and checking if all memberships
    exist, optionally creating them
    """

    def add_arguments(self, parser):
        parser.add_argument("--create", action="store_true")

    @transaction.atomic
    def handle(self, *args, **options):
        for person in Person.objects.all():
            version = json.loads(person.versions)[0]
            for ballot_paper_id, candidacy in (
                version["data"].get("candidacies", {}).items()
            ):
                try:
                    Membership.objects.get(
                        ballot__ballot_paper_id=ballot_paper_id,
                        person_id=person.pk,
                    )
                except Membership.DoesNotExist:
                    membership_detail = [
                        str(person.pk),
                        ballot_paper_id,
                        candidacy.get("party"),
                    ]
                    print("\t".join(membership_detail))
                    # Make sure no other candidacies exist for this
                    # (person, election)
                    ballot = Ballot.objects.get(ballot_paper_id=ballot_paper_id)
                    memberships_for_election = Membership.objects.filter(
                        person=person, ballot__election=ballot.election
                    )
                    if memberships_for_election.exists():
                        self.stderr.write(
                            "Can't create Membership for ({}, {}) – duplicate election".format(
                                person.pk, ballot_paper_id
                            )
                        )
                        continue
                    if options["create"]:
                        party = Party.objects.get(ec_id=candidacy["party"])
                        Membership.objects.create(
                            ballot=ballot,
                            post=ballot.post,
                            person_id=person.pk,
                            party=party,
                            elected=candidacy.get("elected", None),
                            party_list_position=candidacy.get(
                                "party_list_position", None
                            ),
                        )
