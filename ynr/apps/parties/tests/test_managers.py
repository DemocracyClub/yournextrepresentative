"""
Test some of the basic model use cases

"""
from collections import namedtuple

from django.test import TestCase
from django.utils import timezone
from parties.models import Party
from parties.tests.fixtures import DefaultPartyFixtures

from .factories import PartyFactory

PartyDate = namedtuple(
    "PartyDate", ["ec_id", "name", "date_registered", "date_deregistered"]
)
PARTY_DATES = (
    PartyDate("PP01", "Long running still exists party", "2001-05-05", None),
    PartyDate("PP02", "Deregistered Party", "2001-05-05", "2003-05-05"),
    PartyDate("PP03", "New existing party", "2010-05-05", None),
)


class TestPartyManager(DefaultPartyFixtures, TestCase):
    def setUp(self):
        PartyFactory.reset_sequence()
        for party_date in PARTY_DATES:
            PartyFactory(**party_date._asdict())

    def test_parties(self):
        self.assertEqual(Party.objects.count(), 5)

    def test_current_parties(self):
        self.assertEqual(Party.objects.current().count(), 4)
        self.assertTrue(
            "PP01" in Party.objects.current().values_list("ec_id", flat=True)
        )

    def test_active_for_date(self):
        date = timezone.datetime(2001, 10, 5)
        qs = Party.objects.active_for_date(date)
        self.assertEqual(qs.count(), 4)

        # Before any known parties (apart from Indepentant)!
        date = timezone.datetime(2001, 1, 5)
        qs = Party.objects.active_for_date(date)
        self.assertEqual(qs.count(), 2)

    def test_active_in_last_year(self):
        # only PP03 should not exist
        qs = Party.objects.active_in_last_year(
            date=timezone.datetime(2003, 5, 6)
        )
        self.assertEqual(qs.count(), 4)
        self.assertFalse(qs.filter(ec_id="PP03").exists())

        # PP03 should not exist because not registered yet
        # PP02 should not exist because it was deregistered over a year ago
        qs = Party.objects.active_in_last_year(
            date=timezone.datetime(2004, 5, 6)
        )
        self.assertEqual(qs.count(), 3)
        self.assertFalse(qs.filter(ec_id="PP03").exists())
        self.assertFalse(qs.filter(ec_id="PP02").exists())
