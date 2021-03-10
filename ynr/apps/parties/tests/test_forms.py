from django.core.exceptions import ValidationError
from django.test import TestCase

from django.forms import forms

from parties.forms import PartyIdentifierField
from parties.tests.factories import PartyFactory
from parties.tests.fixtures import DefaultPartyFixtures


class TestPartyFields(DefaultPartyFixtures, TestCase):
    def setUp(self):
        class DefaultPartyForm(forms.Form):
            party = PartyIdentifierField(required=False)

        self.default_form = DefaultPartyForm

    def test_field_html(self):
        form = self.default_form()
        self.assertHTMLEqual(
            form.as_p(),
            """
            <p>
                <label for="id_party_0">Party:</label>
                <select name="party_0" id="id_party_0">
                    <option value="" selected>
                    </option>
                </select>
                <input type="text" name="party_1" id="id_party_1">
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
            {
                "party": [
                    "Select a valid choice. not a party is not one of the available choices.",
                    "'not a party' is not a current party identifier",
                ]
            },
        )
        self.assertFalse(form.is_valid())

    def test_party_selected(self):
        PartyFactory(ec_id="PP12", name="New party")
        PartyFactory(
            ec_id="PP13",
            name="New party without candidates",
            current_candidates=0,
        )
        field = PartyIdentifierField(required=False)
        self.assertEqual(
            field.fields[0].choices, [("", ""), ("PP12", "New party")]
        )

    def test_char_input_returned_if_values_in_both_fields(self):
        party1 = PartyFactory(ec_id="PP12", name="New party")
        party2 = PartyFactory(
            ec_id="PP13",
            name="New party without candidates",
            current_candidates=0,
        )

        field = PartyIdentifierField(required=False)
        # We should get the last value from right to left
        self.assertEqual(field.clean(["", "PP13"]), party2)
        self.assertEqual(field.clean(["PP12", "PP13"]), party2)
        self.assertEqual(field.clean(["PP12", ""]), party1)

    def test_validation_errors(self):
        PartyFactory(ec_id="PP12", name="New party")
        PartyFactory(
            ec_id="PP13",
            name="New party without candidates",
            current_candidates=0,
        )

        field = PartyIdentifierField(required=False)
        msg = (
            "'Select a valid choice. PP99 is not one of the available choices.'"
        )
        with self.assertRaisesMessage(ValidationError, msg):
            field.clean(["PP99", ""])

        msg = "'PP99' is not a current party identifier"
        with self.assertRaisesMessage(ValidationError, msg):
            field.clean(["", "PP99"])
