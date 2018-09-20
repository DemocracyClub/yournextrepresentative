from datetime import date, timedelta

from django.test import TestCase

from candidates.tests.factories import (
    ElectionFactory,
    ParliamentaryChamberFactory,
)

from elections.models import Election


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
