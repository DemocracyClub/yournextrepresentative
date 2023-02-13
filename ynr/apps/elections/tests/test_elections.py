import pytest
from datetime import date, timedelta
from django.test import TestCase

from candidates.tests.factories import (
    ElectionFactory,
    ParliamentaryChamberFactory,
)
from elections.models import Election
from django.template.defaultfilters import date as date_filter

from ynr.settings.constants.formats.en.formats import (
    DATE_FORMAT,
    SHORT_DATE_FORMAT,
)


class ElectionTests(TestCase):
    def setUp(self):
        org = ParliamentaryChamberFactory.create()

        self.election = ElectionFactory.create(
            slug="2015",
            name="2015 Election",
            election_date=date.today(),
            organization=org,
        )

    def test_are_upcoming_elections(self):
        self.assertTrue(Election.objects.are_upcoming_elections())

        self.election_date = date.today() + timedelta(days=1)
        self.election.save()
        self.assertTrue(Election.objects.are_upcoming_elections())

        self.election.current = False
        self.election.save()
        self.assertFalse(Election.objects.are_upcoming_elections())

        self.election.current = True
        self.election.election_date = date.today() - timedelta(days=1)
        self.election.save()
        self.assertFalse(Election.objects.are_upcoming_elections())

    @pytest.mark.freeze_time("5 December 2022")
    def test_election_date_format(self):
        # assert that today's date is formatted according to DATE_FORMAT
        self.assertEqual(
            date_filter(self.election.election_date, DATE_FORMAT),
            "5 December 2022",
        )

    @pytest.mark.freeze_time("5 December 2022")
    def test_short_election_date_format(self):
        # assert that a given ballot date is formatted according to SHORT_DATE_FORMAT
        self.assertEqual(
            date_filter(self.election.election_date, SHORT_DATE_FORMAT),
            "5 Dec 2022",
        )
