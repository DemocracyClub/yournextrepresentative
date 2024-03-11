from candidatebot.helpers import CandidateBot
from candidates.models import LoggedAction
from candidates.tests.uk_examples import UK2015ExamplesMixin
from django.conf import settings
from django.contrib.auth.models import User
from django.db import IntegrityError
from django.test import TestCase
from people.tests.factories import PersonFactory


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
        self.assertEqual(self.person.versions, [])
        person = bot.edit_fields(edit, "a source", save=True)
        expected = {
            "blue_sky_url": "",
            "biography": "",
            "birth_date": "",
            "blog_url": "",
            "death_date": "",
            "email": "tessa@example.com",
            "extra_fields": {"favourite_biscuits": ""},
            "facebook_page_url": "",
            "facebook_personal_url": "",
            "gender": "",
            "homepage_url": "",
            "honorific_prefix": "",
            "honorific_suffix": "",
            "id": "2009",
            "instagram_url": "",
            "linkedin_url": "",
            "name": "Tessa Jowell",
            "other_names": [],
            "other_url": "",
            "party_ppc_page_url": "",
            "candidacies": {},
            "threads_url": "",
            "tiktok_url": "",
            "twitter_username": "",
            "mastodon_username": "",
            "wikidata_id": "",
            "wikipedia_url": "",
            "youtube_profile": "",
        }
        got = person.versions
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
            bot.edit_field("linkedin", "https://linkedin.com/CandidateBot")

    def test_update_field(self):
        self.person.tmp_person_identifiers.create(
            value_type="email", value="foo@bar.com"
        )
        self.assertEqual(self.person.get_email, "foo@bar.com")
        bot = CandidateBot(self.person.pk)
        bot.edit_field("email", "foo@example.com", update=True)
        person = bot.save("a source")
        self.assertEqual(person.get_email, "foo@example.com")

        # Now test this doesn't work if update==False
        bot = CandidateBot(self.person.pk)
        with self.assertRaises(IntegrityError):
            bot.edit_field("email", "foo@bar.com", update=False)

        # Now test we can ignore the above error if we want to
        bot = CandidateBot(self.person.pk)
        bot.IGNORE_ERRORS = True
        bot.edit_field("email", "foo@bar.com", update=False)
        person = bot.save("a source")
        # The edit failed, but didn't raise an error
        self.assertEqual(person.get_email, "foo@example.com")

    def test_edit_invalid_value(self):
        # First, make sure we can't do this
        bot = CandidateBot(self.person.pk)
        with self.assertRaises(ValueError):
            bot.edit_field("email", "INVALID")

        # Now, ignore errors and verify nothing changes, but no errors
        # are raised
        bot = CandidateBot(self.person.pk)
        bot.IGNORE_ERRORS = True
        bot.edit_field("email", "INVALID")
        person = bot.save("a source")
        self.assertEqual(person.get_email, None)

    def test_identical_edit_no_logged_action(self):
        self.assertFalse(LoggedAction.objects.exists())
        bot = CandidateBot(self.person.pk, ignore_errors=True, update=True)
        bot.add_email("foo@bar.com")
        bot.save("a source")
        self.assertEqual(LoggedAction.objects.count(), 1)
        bot = CandidateBot(self.person.pk, ignore_errors=True)
        bot.add_email("foo@bar.com")
        bot.save("a source")
        self.assertEqual(LoggedAction.objects.count(), 1)
