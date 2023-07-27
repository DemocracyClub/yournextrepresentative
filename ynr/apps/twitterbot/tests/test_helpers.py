from unittest.mock import patch

from candidates.models import LoggedAction
from candidates.tests.auth import TestUserMixin
from django.test import override_settings
from django.test.testcases import TestCase
from people.tests.factories import PersonIdentifierFactory
from twitterbot.helpers import TwitterBot


class TestTwitterBot(TestUserMixin, TestCase):
    def setUp(self) -> None:
        self.twitterbot = TwitterBot()

    @override_settings(TWITTER_APP_ONLY_BEARER_TOKEN="footoken")
    @patch("twitterbot.helpers.requests")
    def test_is_user_suspended_true(self, mock_requests):
        mock_requests.get.return_value.json.return_value = {
            "errors": [{"code": 63, "message": "User has been suspended."}]
        }

        result = self.twitterbot.is_user_suspended(screen_name="suspendeduser")
        mock_requests.get.assert_called_once_with(
            "https://api.twitter.com/1.1/users/show.json",
            params={"screen_name": "suspendeduser"},
            headers={"Authorization": "Bearer footoken"},
        )
        assert result is True

    @override_settings(TWITTER_APP_ONLY_BEARER_TOKEN="footoken")
    @patch("twitterbot.helpers.requests")
    def test_is_user_suspended_false(self, mock_requests):
        mock_requests.get.return_value.json.return_value = {}

        result = self.twitterbot.is_user_suspended(screen_name="unknownuser")
        mock_requests.get.assert_called_once_with(
            "https://api.twitter.com/1.1/users/show.json",
            params={"screen_name": "unknownuser"},
            headers={"Authorization": "Bearer footoken"},
        )
        assert result is False

    def test_handle_suspended_initial_suspension(self):
        identifier = PersonIdentifierFactory()
        assert identifier.extra_data == {}
        assert LoggedAction.objects.count() == 0

        self.twitterbot.handle_suspended(identifier=identifier)

        assert identifier.extra_data == {
            "status": "suspended",
            "suspension_count": 1,
        }
        assert LoggedAction.objects.count() == 1

    def test_handle_suspended_already_suspended(self):
        identifier = PersonIdentifierFactory(
            extra_data={"status": "suspended", "suspension_count": 1}
        )
        with patch.object(self.twitterbot, "save") as save:
            self.twitterbot.handle_suspended(identifier=identifier)

            assert identifier.extra_data == {
                "status": "suspended",
                "suspension_count": 1,
            }
            save.assert_not_called()

    def test_handle_suspended_new_suspension(self):
        identifier = PersonIdentifierFactory(
            extra_data={"status": "active", "suspension_count": 1}
        )
        self.twitterbot.handle_suspended(identifier=identifier)

        assert identifier.extra_data == {
            "status": "suspended",
            "suspension_count": 2,
        }
