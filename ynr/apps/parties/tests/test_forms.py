from unittest.mock import patch
from django.core.exceptions import ValidationError
from django.test import TestCase

from django import forms

from candidates.tests.factories import MembershipFactory
from candidates.tests.uk_examples import UK2015ExamplesMixin
from parties.forms import (
    PartyIdentifierField,
    PopulatePartiesMixin,
    PreviousPartyAffiliationsField,
)
from parties.models import Party
from parties.tests.factories import PartyFactory
from parties.tests.fixtures import DefaultPartyFixtures
from people.forms.fields import CurrentUnlockedBallotsField
from people.forms.forms import PersonMembershipForm
from people.tests.factories import PersonFactory


class TestPartyFields(UK2015ExamplesMixin, DefaultPartyFixtures, TestCase):
    def setUp(self):
        Party.objects.all().delete()

        class DefaultPartyForm(forms.Form):
            party = PartyIdentifierField(
                required=False, choices=Party.objects.default_party_choices()
            )

        self.default_form = DefaultPartyForm

    def test_field_html(self):
        form = self.default_form()
        self.assertHTMLEqual(
            form.as_p(),
            """
            <p>
                <label>Party:</label>
                <select class="party_widget_select" disabled name="party_0"
                id="id_party_0">
                    <option value="" selected>
                    </option>
                </select>
                <input class="party_widget_input" type="text" name="party_1"
                id="id_party_1">
            </p>
            """,
        )

    def test_validate_party_ids(self):
        form = self.default_form(
            {"party_0": "not a party", "party_1": "not a party"}
        )
        form.full_clean()
        self.assertDictEqual(
            form.errors,
            {"party": ["'not a party' is not a current party identifier"]},
        )
        self.assertFalse(form.is_valid())

    def test_party_selected(self):
        PartyFactory(ec_id="PP12", name="New party")
        PartyFactory(
            ec_id="PP13",
            name="New party without candidates",
            current_candidates=0,
        )
        field = PartyIdentifierField(
            required=False, choices=Party.objects.default_party_choices()
        )
        self.assertEqual(
            field.fields[0].choices,
            [
                ("", {"label": ""}),
                ("PP12", {"label": "New party", "register": "GB"}),
            ],
        )

    def test_char_input_returned_if_values_in_both_fields(self):
        party1 = PartyFactory(ec_id="PP12", name="New party")
        party2 = PartyFactory(
            ec_id="PP13",
            name="New party without candidates",
            current_candidates=0,
        )

        field = PartyIdentifierField(
            required=False, choices=Party.objects.default_party_choices()
        )
        # We should get the last value from right to left
        self.maxDiff = None
        self.assertEqual(
            field.clean(["", "PP13"]),
            {
                "description_obj": None,
                "description_id": None,
                "description_text": None,
                "party_obj": party2,
                "party_id": "PP13",
                "party_name": "New party without candidates",
            },
        )
        self.assertEqual(
            field.clean(["PP12", "PP13"]),
            {
                "description_obj": None,
                "description_id": None,
                "description_text": None,
                "party_obj": party2,
                "party_id": "PP13",
                "party_name": "New party without candidates",
            },
        )
        self.assertEqual(
            field.clean(["PP12", ""]),
            {
                "description_obj": None,
                "description_id": None,
                "description_text": None,
                "party_obj": party1,
                "party_id": "PP12",
                "party_name": "New party",
            },
        )

    def test_validation_errors(self):
        PartyFactory(ec_id="PP12", name="New party")
        PartyFactory(
            ec_id="PP13",
            name="New party without candidates",
            current_candidates=0,
        )

        field = PartyIdentifierField(required=False)
        msg = "'PP99' is not a current party identifier"
        with self.assertRaisesMessage(ValidationError, msg):
            field.clean(["PP99", ""])

        msg = "'PP99' is not a current party identifier"
        with self.assertRaisesMessage(ValidationError, msg):
            field.clean(["", "PP99"])

    def test_select_with_initial_contains_party(self):
        """
        If a user has selected a party previously, it should be a selected
        option in the dropdown, even if it normally wouldn't be in there
        """
        PartyFactory(ec_id="PP12", name="New party")
        PartyFactory(
            ec_id="PP13",
            name="New party without candidates",
            current_candidates=0,
        )
        field = PartyIdentifierField(
            required=False, choices=Party.objects.default_party_choices()
        )
        # Make sure PP13 isn't in the default list
        self.assertEqual(
            field.fields[0].choices,
            [
                ("", {"label": ""}),
                ("PP12", {"label": "New party", "register": "GB"}),
            ],
        )

        class PartyForm(PopulatePartiesMixin, forms.Form):
            ballot = CurrentUnlockedBallotsField()
            party = PartyIdentifierField(
                required=False, require_all_fields=False
            )

        form = PartyForm(initial={"party": ["", "PP13"]})
        self.assertEqual(
            form["party"].field.fields[0].choices,
            [
                ("", {"label": ""}),
                ("PP12", {"label": "New party", "register": "GB"}),
                (
                    "PP13",
                    {"label": "New party without candidates", "register": "GB"},
                ),
            ],
        )

    def test_update_model_form_populates_other_parties(self):
        """
        PersonMembershipForm uses PopulatePartiesMixin, so should add our new
        party to the default choices

        """
        new_party = PartyFactory(ec_id="PP12", name="New party")
        person = PersonFactory()
        membership = MembershipFactory(
            ballot=self.dulwich_post_ballot, person=person, party=new_party
        )
        form = PersonMembershipForm(instance=membership)
        self.assertEqual(
            form["party_identifier"].field.fields[0].choices[1],
            ("PP12", {"label": "New party", "register": "GB"}),
        )


class TestPreviousPartyAffiliationsField(
    UK2015ExamplesMixin, DefaultPartyFixtures, TestCase
):
    def test_widget_attrs(self):
        field = PreviousPartyAffiliationsField()
        self.assertEqual(
            field.widget_attrs(None), {"class": "previous-party-affiliations"}
        )

    def test_get_previous_party_affiliations_choices_called_on_init(self):
        """
        Test when get_previous_party_affiliations_choices gets called
        and does not
        """
        with patch.object(
            PreviousPartyAffiliationsField,
            "get_previous_party_affiliations_choices",
        ) as mock:
            PreviousPartyAffiliationsField(choices=[("foo", "Bar")])
            mock.assert_not_called()
            PreviousPartyAffiliationsField()
            mock.assert_called_once()

    def test_get_previous_party_affiliations_choices(self):
        # test without a membership
        field = PreviousPartyAffiliationsField()
        self.assertEqual(field.get_previous_party_affiliations_choices(), [])

        membership = MembershipFactory(
            ballot=self.dulwich_post_ballot,
            person=PersonFactory(),
            party=self.labour_party,
        )
        field = PreviousPartyAffiliationsField(membership=membership)
        self.assertEqual(field.get_previous_party_affiliations_choices(), [])

        # test a membership for non-welsh ballot
        membership = MembershipFactory(
            ballot=self.dulwich_post_ballot,
            person=PersonFactory(),
            party=self.labour_party,
        )
        field = PreviousPartyAffiliationsField(membership=membership)
        self.assertEqual(field.get_previous_party_affiliations_choices(), [])

        # test a membership for welsh-run ballot
        membership = MembershipFactory(
            ballot=self.senedd_ballot,
            person=PersonFactory(),
            party=self.labour_party,
        )
        expected = [
            (party.ec_id, party.name) for party in Party.objects.register("GB")
        ]
        field = PreviousPartyAffiliationsField(membership=membership)
        self.assertEqual(
            set(field.get_previous_party_affiliations_choices()), set(expected)
        )
