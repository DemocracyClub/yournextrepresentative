import sys
from io import StringIO

from django.core.management import call_command
from django.test import TestCase
from freezegun import freeze_time
from parties.models import Party
from parties.tests.factories import PartyFactory


class TestPartiesMakeJointParty(TestCase):
    def setUp(self):
        PartyFactory(ec_id="PP01", name="Party One")
        PartyFactory(ec_id="PP02", name="Party Two")

    @freeze_time("2024-06-01")
    def test_make_joint_party(self):
        call_command("parties_make_joint_party", "PP01", "PP02")

        joint_party = Party.objects.get(ec_id="joint-party:1-2")
        self.assertEqual(joint_party.name, "Party One and Party Two")
        self.assertEqual(joint_party.date_registered.isoformat(), "2024-06-01")

    def test_joint_party_exists(self):
        out = StringIO()
        sys.stderr = out

        call_command("parties_make_joint_party", "PP01", "PP02")
        call_command("parties_make_joint_party", "PP01", "PP02")
        sys.stderr = sys.__stderr__

        self.assertIn("already exists", out.getvalue())
        # There should only be 3 parties despite running the command twice
        self.assertEqual(Party.objects.count(), 3)

    def test_date_registered_flag(self):
        call_command(
            "parties_make_joint_party",
            "PP01",
            "PP02",
            "--date-registered",
            "2026-01-01",
        )

        joint_party = Party.objects.get(ec_id="joint-party:1-2")
        self.assertEqual(joint_party.date_registered.isoformat(), "2026-01-01")
