from unittest import TestCase

import pytest
from candidates.models.popolo_extra import Ballot
from candidates.tests.factories import (
    ElectionFactory,
    MembershipFactory,
    PostFactory,
)
from django.core.management import call_command
from parties.tests.factories import PartyFactory
from people.tests.factories import PersonFactory, PersonIdentifierFactory


class TestPersonIdentifiers(TestCase):
    def setUp(self):
        self.person = PersonFactory.create()
        # 200 example
        PersonIdentifierFactory.create(
            person=self.person,
            value="https://en.wikipedia.org/wiki/Rishi_Sunak",
            value_type="https://en.wikipedia_url",
        )
        # 404 example
        PersonIdentifierFactory.create(
            person=self.person,
            value="http://www.conservatives.com/about/our-team/example.com",
            value_type="party_ppc_page_url",
        )
        post = PostFactory.create(slug="parl.2024-07-04")

        election = ElectionFactory.create(
            slug="parl.2024-07-04",
            election_date="2024-07-04",
            name="2024 General Election",
        )
        ballot = Ballot.objects.create(
            election=election, post=post, ballot_paper_id="parl.2024-07-04"
        )
        party = PartyFactory.create()
        MembershipFactory.create(
            person=self.person,
            post=post,
            party=party,
            ballot=ballot,
        )

    @pytest.mark.django_db
    def test_remove_inactive_person_identifiers(self):
        self.assertEqual(len(self.person.get_all_identifiers), 2)
        self.assertEqual(
            self.person.get_all_identifiers[0].value,
            "https://en.wikipedia.org/wiki/Rishi_Sunak",
        )
        self.assertEqual(
            self.person.get_all_identifiers[1].value,
            "http://www.conservatives.com/about/our-team/example.com",
        )
        call_command("remove_inactive_person_links")
        self.person.refresh_from_db()
        self.assertEqual(len(self.person.get_all_identifiers), 1)
        self.assertEqual(
            self.person.get_all_identifiers[0].value,
            "https://en.wikipedia.org/wiki/Rishi_Sunak",
        )
