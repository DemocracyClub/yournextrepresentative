"""
Test some of the basic model use cases

"""
from django.core.files.storage import DefaultStorage
from django.conf import settings
from django.test import TestCase

from candidates.tests.helpers import TmpMediaRootMixin

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
        print(party.emblems.first().image.url)
        self.assertTrue(
            party.emblems.first().image.url.startswith(
                "{}/emblems/PP0/0_example".format(settings.MEDIA_ROOT)
            )
        )

        # Add a default image and assert it's the deafult on the party
        PartyEmblemFactory(party=party, __sequence=99, default=True)
        self.assertTrue(
            party.default_emblem.image.url.startswith(
                "{}/emblems/PP0/99_example".format(settings.MEDIA_ROOT)
            )
        )
