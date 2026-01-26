from datetime import date

from candidates.models import PersonRedirect
from candidates.models.popolo_extra import Ballot
from django.conf import settings
from django.core.management.base import BaseCommand
from django.db import transaction
from elections.models import Election
from parties.models import Party
from popolo.models import Membership, Organization, Post


class Command(BaseCommand):
    """
    Create data for training sessions.

    This script assumes the existence of:

    - `Organization` object for `local-authority:havering`
    - `Post` objects for the 2022-onwards wards of Havering
    - `Party` objects for:
        - Conservative Party (PP52)
        - Labour Party (PP53)
        - Labour & Co-op Party (joint-party:53-119)
    - Various `Person` objects
    """

    help = "Create data for training sessions"

    def resolve_person_id(self, person_id):
        try:
            return PersonRedirect.objects.get(
                old_person_id=person_id
            ).new_person_id
        except PersonRedirect.DoesNotExist:
            return person_id

    def create_membership(self, person_id, party, ballot_id, org):
        post = (
            Post.objects.all()
            .filter(organization=org, start_date="2022-05-05")
            .get(slug=ballot_id.split(".")[2])
        )
        ballot = Ballot.objects.get(ballot_paper_id=ballot_id)

        membership = Membership(
            label="",
            role="Candidate",
            person_id=person_id,
            party=party,
            party_description=None,
            party_name=party.name,
            party_description_text="",
            post=post,
            elected=None,
            party_list_position=None,
            ballot=ballot,
            deselected=False,
            deselected_source="",
        )
        membership.save()

    @transaction.atomic
    def handle(self, *args, **options):
        if settings.DC_ENVIRONMENT == "production":
            raise Exception(
                "Abort: This command imports fake data. Don't run this in the production environment."
            )

        polling_day = date(2026, 5, 8)
        polling_day_text = "2026-05-08"

        org = Organization.objects.all().get(slug="local-authority:havering")

        # Clear existing before we create
        # This will also nuke the child ballots and memberships
        Election.objects.filter(
            slug=f"local.havering.{polling_day_text}"
        ).delete()

        # election
        election = Election(
            slug=f"local.havering.{polling_day_text}",
            for_post_role="Local elections",
            winner_membership_role=None,
            candidate_membership_role="Candidate",
            election_date=polling_day,
            name="Havering local election (training)",
            current=True,
            use_for_candidate_suggestions=False,
            organization=org,
            party_lists_in_use=False,
            people_elected_per_post=1,
            default_party_list_members_to_show=0,
            show_official_documents=True,
            ocd_division="",
            description="",
            modgov_url=None,
        )
        election.save()

        # ballots
        ballot_ids = [
            (f"local.havering.beam-park.{polling_day_text}", 2),
            (f"local.havering.cranham.{polling_day_text}", 3),
            (f"local.havering.elm-park.{polling_day_text}", 3),
            (f"local.havering.emerson-park.{polling_day_text}", 2),
            (f"local.havering.gooshays.{polling_day_text}", 3),
            (f"local.havering.hacton.{polling_day_text}", 2),
            (f"local.havering.harold-wood.{polling_day_text}", 3),
            (f"local.havering.havering-atte-bower.{polling_day_text}", 3),
            (f"local.havering.heaton.{polling_day_text}", 3),
            (f"local.havering.hylands-harrow-lodge.{polling_day_text}", 3),
            (f"local.havering.marshalls-rise-park.{polling_day_text}", 3),
            (f"local.havering.mawneys.{polling_day_text}", 3),
            (f"local.havering.rainham-wennington.{polling_day_text}", 3),
            (f"local.havering.rush-green-crowlands.{polling_day_text}", 3),
            (f"local.havering.south-hornchurch.{polling_day_text}", 2),
            (f"local.havering.squirrels-heath.{polling_day_text}", 3),
            (f"local.havering.st-albans.{polling_day_text}", 2),
            (f"local.havering.st-andrews.{polling_day_text}", 3),
            (f"local.havering.st-edwards.{polling_day_text}", 3),
            (f"local.havering.upminster.{polling_day_text}", 3),
        ]

        for ballot_id, winner_count in ballot_ids:
            post = (
                Post.objects.all()
                .filter(organization=org, start_date="2022-05-05")
                .get(slug=ballot_id.split(".")[2])
            )
            ballot = Ballot(
                ballot_paper_id=ballot_id,
                post=post,
                election=election,
                candidates_locked=False,
                winner_count=winner_count,
                cancelled=False,
                replaces=None,
                voting_system=Ballot.VOTING_SYSTEM_FPTP,
                tags={},
                by_election_reason="",
            )
            ballot.save()

        # valid candidates - these people are all on the SOPN
        conservatives = [
            (f"local.havering.heaton.{polling_day_text}", 91359),
            (f"local.havering.heaton.{polling_day_text}", 91363),
            (f"local.havering.heaton.{polling_day_text}", 43250),
            (f"local.havering.mawneys.{polling_day_text}", 42931),
            (f"local.havering.mawneys.{polling_day_text}", 42935),
            (f"local.havering.mawneys.{polling_day_text}", 42937),
            (f"local.havering.gooshays.{polling_day_text}", 91387),
            (f"local.havering.gooshays.{polling_day_text}", 42361),
            (f"local.havering.gooshays.{polling_day_text}", 91389),
        ]
        labour_and_coop = [
            (f"local.havering.heaton.{polling_day_text}", 91360),
            (f"local.havering.heaton.{polling_day_text}", 42820),
            (f"local.havering.heaton.{polling_day_text}", 91366),
            (f"local.havering.gooshays.{polling_day_text}", 91385),
            (f"local.havering.gooshays.{polling_day_text}", 4356),
            (f"local.havering.gooshays.{polling_day_text}", 91391),
        ]
        conservative_party = Party.objects.get(ec_id="PP52")
        labour_party = Party.objects.get(ec_id="PP53")
        labour_and_coop_party = Party.objects.get(ec_id="joint-party:53-119")

        for ballot_id, person_id in conservatives:
            self.create_membership(
                self.resolve_person_id(person_id),
                conservative_party,
                ballot_id,
                org,
            )

        for ballot_id, person_id in labour_and_coop:
            self.create_membership(
                self.resolve_person_id(person_id),
                labour_and_coop_party,
                ballot_id,
                org,
            )

        # invalid candidates

        # This person is standing for this party, but they are really
        # standing in St Alban's, not St Andrew's. Whoopsie
        self.create_membership(
            person_id=self.resolve_person_id(43037),
            party=conservative_party,
            ballot_id=f"local.havering.st-andrews.{polling_day_text}",
            org=org,
        )

        # This person is standing in this ward, but we've put them down as
        # standing for Labour and Co-operative Party (joint-party:53-119)
        # whereas they are actually standing for Labour Party (PP53).
        # Easy mistake, but we will need to fix it.
        self.create_membership(
            person_id=self.resolve_person_id(91518),
            party=labour_and_coop_party,
            ballot_id=f"local.havering.st-andrews.{polling_day_text}",
            org=org,
        )

        # This person is not standing in this election at all
        self.create_membership(
            person_id=self.resolve_person_id(4012),
            party=labour_party,
            ballot_id=f"local.havering.st-andrews.{polling_day_text}",
            org=org,
        )
