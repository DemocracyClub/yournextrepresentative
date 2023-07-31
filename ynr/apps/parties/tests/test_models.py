"""
Test some of the basic model use cases

"""
from candidates.tests.helpers import TmpMediaRootMixin
from django.conf import settings
from django.core.files.storage import DefaultStorage
from django.test import TestCase

from .factories import PartyEmblemFactory, PartyFactory


class TestPartyModels(TmpMediaRootMixin, TestCase):
    def setUp(self):
        self.storage = DefaultStorage()
        PartyFactory.reset_sequence()

    def test_party_str(self):
        party = PartyFactory()
        self.assertEqual(str(party), "Party 0 (PP0)")

    def test_party_emblem(self):
        party = PartyFactory()
        PartyEmblemFactory.create_batch(3, party=party)
        self.assertEqual(party.emblems.count(), 3)
        first_emblem = party.emblems.first()
        self.assertEqual(
            first_emblem.image.url,
            f"{settings.MEDIA_ROOT}/emblems/PP0/{first_emblem.ec_emblem_id}_example.jpg",
        )

        # Add a default image and assert it's the deafult on the party
        PartyEmblemFactory(party=party, __sequence=99, default=True)
        self.assertEqual(
            party.default_emblem.image.url,
            f"{settings.MEDIA_ROOT}/emblems/PP0/99_example.jpg",
        )
