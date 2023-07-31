from unittest import skip

from django.test import TestCase
from django.test.utils import override_settings
from people.forms.forms import BasePersonForm, UpdatePersonForm
from people.tests.factories import PersonFactory

from .uk_examples import UK2015ExamplesMixin


@override_settings(TWITTER_APP_ONLY_BEARER_TOKEN=None)
class TestValidators(UK2015ExamplesMixin, TestCase):
    def setUp(self):
        super().setUp()
        self.person = PersonFactory.create(name="John Doe")

    @skip("PersonIdentifiers are on Person Form")
    def test_malformed_email(self):
        form = BasePersonForm(
            {"name": "John Bercow", "email": "foo bar!"},
            initial={"person": self.person},
        )
        self.assertFalse(form.is_valid())
        self.assertEqual(
            form.errors, {"email": ["Enter a valid email address."]}
        )

    @skip("Until rebased over upstream master")
    def test_update_person_form_standing_no_party_no_constituency(self):
        form = UpdatePersonForm(
            {
                "name": "John Doe",
                "source": "Just testing...",
                "standing_2015": "standing",
            },
            initial={"person": self.person},
        )
        self.assertFalse(form.is_valid())
        self.assertEqual(
            form.errors,
            {
                "__all__": [
                    "If you mark the candidate as standing in the 2015 General Election, you must select a post"
                ]
            },
        )

    @skip("Until rebased over upstream master")
    def test_update_person_form_standing_no_party_but_gb_constituency(self):
        form = UpdatePersonForm(
            {
                "name": "John Doe",
                "source": "Just testing...",
                "standing_2015": "standing",
                "constituency_2015": "65808",
            },
            initial={"person": self.person},
        )
        self.assertFalse(form.is_valid())
        self.assertEqual(
            form.errors,
            {
                "__all__": [
                    "You must specify a party for the 2015 General Election"
                ]
            },
        )

    def test_update_person_form_standing_party_and_gb_constituency(self):
        form = UpdatePersonForm(
            {
                "name": "John Doe",
                "source": "Just testing...",
                "standing_2015": "standing",
                "constituency_2015": "65808",
                "party_GB_2015": self.conservative_party.id,
            },
            initial={"person": self.person},
        )
        self.assertTrue(form.is_valid())

    # When 'not-standing' is selected, it shouldn't matter whether you
    # specify party of constituency:

    def test_update_person_form_not_standing_no_party_no_constituency(self):
        form = UpdatePersonForm(
            {
                "name": "John Doe",
                "source": "Just testing...",
                "standing_2015": "not-standing",
            },
            initial={"person": self.person},
        )
        self.assertTrue(form.is_valid())

    def test_update_person_form_not_standing_no_party_but_gb_constituency(self):
        form = UpdatePersonForm(
            {
                "name": "John Doe",
                "source": "Just testing...",
                "standing_2015": "not-standing",
                "constituency_2015": "65808",
            },
            initial={"person": self.person},
        )
        self.assertTrue(form.is_valid())

    def test_update_person_form_not_standing_party_and_gb_constituency(self):
        form = UpdatePersonForm(
            {
                "name": "John Doe",
                "source": "Just testing...",
                "standing_2015": "standing",
                "constituency_2015": "65808",
                "party_GB_2015": self.conservative_party.id,
            },
            initial={"person": self.person},
        )
        self.assertTrue(form.is_valid())

    # Similarly, when 'not-sure' is selected, it shouldn't matter
    # whether you specify party of constituency:

    def test_update_person_form_not_sure_no_party_no_constituency(self):
        form = UpdatePersonForm(
            {
                "name": "John Doe",
                "source": "Just testing...",
                "standing_2015": "not-sure",
            },
            initial={"person": self.person},
        )
        self.assertTrue(form.is_valid())

    def test_update_person_form_not_sure_no_party_but_gb_constituency(self):
        form = UpdatePersonForm(
            {
                "name": "John Doe",
                "source": "Just testing...",
                "standing_2015": "not-sure",
                "constituency_2015": "65808",
            },
            initial={"person": self.person},
        )
        self.assertTrue(form.is_valid())

    def test_update_person_form_not_sure_party_and_gb_constituency(self):
        form = UpdatePersonForm(
            {
                "name": "John Doe",
                "source": "Just testing...",
                "standing_2015": "not-sure",
                "constituency_2015": "65808",
                "party_GB_2015": self.conservative_party.id,
            },
            initial={"person": self.person},
        )
        self.assertTrue(form.is_valid())
