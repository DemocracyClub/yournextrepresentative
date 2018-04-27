import json

from django.test import TestCase
from django.conf import settings
from django.contrib.auth.models import User

from candidatebot.helpers import CandidateBot
from candidates.models import LoggedAction
from candidates.tests.factories import PersonExtraFactory
from candidates.tests.uk_examples import UK2015ExamplesMixin


class TestCandidateBot(UK2015ExamplesMixin, TestCase):
    def setUp(self):
        super(TestCandidateBot, self).setUp()
        User.objects.create(username=settings.CANDIDATE_BOT_USERNAME)
        self.person_extra = PersonExtraFactory.create(
            base__id='2009',
            base__name='Tessa Jowell'
        )

    def test_user_smoke_test(self):
        bot = CandidateBot(self.person_extra.base.pk)
        self.assertEqual(bot.user.username, settings.CANDIDATE_BOT_USERNAME)

    def test_edit_fields(self):
        bot = CandidateBot(self.person_extra.base.pk)

        edit = {
            'email': 'tessa@example.com'
        }

        self.assertFalse(LoggedAction.objects.all().exists())
        self.assertEqual(self.person_extra.versions, '[]')
        person = bot.edit_fields(edit, 'a source', save=True)
        expected = {
            "twitter_username": "",
            "standing_in": {},
            "name": "Tessa Jowell",
            "honorific_suffix": "",
            "facebook_page_url": "",
            "gender": "",
            "image": None,
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
            "biography": ""
        }
        got = json.loads(person.extra.versions)
        self.assertEqual(got[0]['data'], expected)
        self.assertEqual(got[0]['information_source'], "a source")
        self.assertEqual(got[0]['username'], settings.CANDIDATE_BOT_USERNAME)
        la = LoggedAction.objects.first()
        self.assertEqual(la.user.username, settings.CANDIDATE_BOT_USERNAME)

    def test_add_email(self):
        bot = CandidateBot(self.person_extra.base.pk)
        bot.add_email("foo@bar.com")
        person = bot.save('a source')
        self.assertEqual(person.email, "foo@bar.com")

    def test_cant_edit_linkedin(self):
        bot = CandidateBot(self.person_extra.base.pk)
        with self.assertRaises(ValueError):
            bot._edit_field("linkedin", "https://linkedin.com/CandidateBot")
