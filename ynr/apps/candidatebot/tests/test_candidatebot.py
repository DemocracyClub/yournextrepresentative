import json

from django.test import TestCase
from django.conf import settings
from django.contrib.auth.models import User

from candidatebot.helpers import CandidateBot
from candidates.models import LoggedAction
from people.tests.factories import PersonFactory
from candidates.tests.uk_examples import UK2015ExamplesMixin


class TestCandidateBot(UK2015ExamplesMixin, TestCase):
    def setUp(self):
        super().setUp()
        User.objects.create(username=settings.CANDIDATE_BOT_USERNAME)
        self.person = PersonFactory.create(id=2009, name="Tessa Jowell")

    def test_user_smoke_test(self):
        bot = CandidateBot(self.person.pk)
        self.assertEqual(bot.user.username, settings.CANDIDATE_BOT_USERNAME)

    def test_edit_fields(self):
        bot = CandidateBot(self.person.pk)

        edit = {"email": "tessa@example.com"}

        self.assertFalse(LoggedAction.objects.all().exists())
        self.assertEqual(self.person.versions, "[]")
        person = bot.edit_fields(edit, "a source", save=True)
        expected = {
            "twitter_username": "",
            "standing_in": {},
            "name": "Tessa Jowell",
            "honorific_suffix": "",
            "facebook_page_url": "",
            "gender": "",
            "facebook_personal_url": "",
            "id": "2009",
            "honorific_prefix": "",
            "linkedin_url": "",
            "homepage_url": "",
            "extra_fields": {"favourite_biscuits": ""},
            "wikipedia_url": "",
            "party_memberships": {},
            "birth_date": "",
            "party_ppc_page_url": "",
            "other_names": [],
            "email": "tessa@example.com",
            "biography": "",
        }
        got = json.loads(person.versions)
        self.assertEqual(got[0]["data"], expected)
        self.assertEqual(got[0]["information_source"], "a source")
        self.assertEqual(got[0]["username"], settings.CANDIDATE_BOT_USERNAME)
        la = LoggedAction.objects.first()
        self.assertEqual(la.user.username, settings.CANDIDATE_BOT_USERNAME)

    def test_add_email(self):
        bot = CandidateBot(self.person.pk)
        bot.add_email("foo@bar.com")
        person = bot.save("a source")
        self.assertEqual(person.get_email, "foo@bar.com")

    def test_cant_edit_linkedin(self):
        bot = CandidateBot(self.person.pk)
        with self.assertRaises(ValueError):
            bot._edit_field("linkedin", "https://linkedin.com/CandidateBot")
