from datetime import datetime

from django.core.management.base import BaseCommand
from parties.importer import make_joint_party_id, make_slug
from parties.models import Party


class Command(BaseCommand):
    help = """
    Create a joint party for 2 existing parties.
    """

    def add_arguments(self, parser):
        parser.add_argument(
            "first_party_ec_id",
            type=str,
            help="The EC ID of the first party. Their name will be first in the joint party name",
        )
        parser.add_argument(
            "second_party_ec_id",
            type=str,
            help="The EC ID of the second party. Their name will be second in the joint party name",
        )
        parser.add_argument(
            "--date-registered",
            type=str,
            default=datetime.today().date().isoformat(),
            help="Optional date registered for the joint party in YYYY-MM-DD format. If not provided, will default to the day the command was run",
        )

    def handle(self, *args, **options):
        parties = self.validate_parties(
            options["first_party_ec_id"], options["second_party_ec_id"]
        )

        if not parties:
            return

        first_party, second_party = parties

        date_registered = options["date_registered"]
        print(f"Making joint party between {first_party} and {second_party}")

        joint_party_id = make_joint_party_id(
            first_party.ec_id, second_party.ec_id
        )

        if Party.objects.filter(ec_id=joint_party_id).exists():
            self.stderr.write(
                f"A party with EC ID {joint_party_id} already exists."
            )
            return

        joint_party_name = f"{first_party.name} and {second_party.name}"
        joint_party_slug = make_slug(joint_party_id)

        Party.objects.create(
            ec_id=joint_party_id,
            name=joint_party_name,
            status="Registered",
            register="GB",
            date_registered=date_registered,
            legacy_slug=joint_party_slug,
        )
        self.stdout.write(
            f"Created joint party {joint_party_name} with EC ID {joint_party_id}"
        )

    def validate_parties(self, first_party_ec_id, second_party_ec_id):
        try:
            first_party = Party.objects.get(ec_id=first_party_ec_id)
            second_party = Party.objects.get(ec_id=second_party_ec_id)
        except Party.DoesNotExist:
            self.stderr.write(
                "One or both of the specified parties do not exist."
            )
            return None

        if (
            first_party.register != "GB"
            or second_party.register != "GB"
            or first_party.status == "Deregistered"
            or second_party.status == "Deregistered"
        ):
            self.stderr.write(
                "Both parties must be registered in the GB register."
            )
            return None

        return first_party, second_party
