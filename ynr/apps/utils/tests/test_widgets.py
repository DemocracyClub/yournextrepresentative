from django.test import TestCase
from utils.widgets import ChoiceOptionWithContext, SelectWithAttrs


class TestSelectWithAttrs(TestCase):
    def test_create_option_with_choice_option_with_context(self):
        widget = SelectWithAttrs()
        label_with_context = ChoiceOptionWithContext(
            label="Option Label",
            attrs={"data-custom": "value"},
        )

        option = widget.create_option(
            name="test_field",
            value="option_value",
            label=label_with_context,
            selected=True,
            index=0,
        )

        # Check that the original attrs are preserved
        self.assertTrue(option["attrs"]["selected"])

        # Check that custom attrs are merged into the option attrs
        self.assertEqual(option["attrs"]["data-custom"], "value")
