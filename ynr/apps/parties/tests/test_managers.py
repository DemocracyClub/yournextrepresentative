"""
Test some of the basic model use cases

"""
from collections import namedtuple

from django.test import TestCase
from django.utils import timezone

from parties.models import Party

from .factories import PartyFactory

PartyDate = namedtuple(
    "PartyDate", ["ec_id", "name", "date_registered", "date_deregistered"]
)
PARTY_DATES = (
    PartyDate("PP01", "Long running still exists party", "2001-05-05", None),
    PartyDate("PP02", "Deregistered Party", "2001-05-05", "2003-05-05"),
    PartyDate("PP03", "New existing party", "2010-05-05", None),
)


class TestPartyManager(TestCase):
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
