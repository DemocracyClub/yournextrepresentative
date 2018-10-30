from mock import patch

from django.test import TestCase

import people.tests.factories
from candidates.election_specific import additional_merge_actions
from candidates.tests import factories


class TestUKSpecificOverride(TestCase):
    @patch("elections.uk.lib.additional_merge_actions")
    def test_uk_version_is_actually_called(self, mock_additional_merge_actions):
        primary = people.tests.factories.PersonFactory(name="Alice")
        secondary = people.tests.factories.PersonFactory(name="Bob")
        additional_merge_actions(primary, secondary)
        mock_additional_merge_actions.assert_called
