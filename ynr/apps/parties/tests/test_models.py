"""
Test some of the basic model use cases

"""
from django.test import TestCase

from .factories import PartyFactory, PartyEmblemFactory


class TestPartyModels(TestCase):
    def setUp(self):
        PartyFactory.reset_sequence()

    def test_party_str(self):
        party = PartyFactory()
        self.assertEqual(str(party), "Party 0 (0)")

    def test_party_emblem(self):
        party = PartyFactory()
        PartyEmblemFactory.create_batch(3, party=party)
        self.assertEqual(party.emblems.count(), 3)
        self.assertTrue(
            party.emblems.first().image.url.startswith(
                "/media/emblems/0/0_example"
            )
        )

        # Add a default image and assert it's the deafult on the party
        PartyEmblemFactory(party=party, __sequence=99, default=True)
        self.assertTrue(
            party.default_emblem.image.url.startswith(
                "/media/emblems/0/99_example"
            )
        )

