from mock import Mock, patch

from django.core.management import call_command
from django.test import TestCase, override_settings

from candidates.tests.auth import TestUserMixin
from people.tests.factories import PersonFactory
from candidates.tests.output import capture_output, split_output


def fake_post_for_username_updater(*args, **kwargs):
    data = kwargs["data"]
    mock_result = Mock()
    if "screen_name" in data:
        if (
            data["screen_name"]
            == "notatwitteraccounteither,notreallyatwitteraccount"
        ):
            mock_result.json.return_value = [
                {
                    "id": 321,
                    "screen_name": "notreallyatwitteraccount",
                    "profile_image_url_https": "https://example.com/a.jpg",
                },
                {
                    "id": 765,
                    "screen_name": "notatwitteraccounteither",
                    "profile_image_url_https": "https://example.com/b.jpg",
                },
            ]
            return mock_result
    if "user_id" in data:
        if data["user_id"] == "987":
            mock_result.json.return_value = [
                {
                    "id": 987,
                    "screen_name": "ascreennamewewereunawareof",
                    "profile_image_url_https": "https://example.com/c.jpg",
                }
            ]
            return mock_result
    raise Exception("No Twitter API stub for {} {}".format(args, kwargs))


@patch("twitterbot.management.twitter.requests")
class TestUpdateTwitterUsernamesCommand(TestUserMixin, TestCase):
    def setUp(self):
        for person_details in [
            {
                "attr": "just_screen_name",
                "name": "Person with just a Twitter screen name",
                # We'll get the API to return 321 for their user_id
                "screen_name": "notreallyatwitteraccount",
            },
            {
                "attr": "just_userid",
                "name": "Person with just a Twitter user ID",
                "user_id": "987",
            },
            {"attr": "no_twitter", "name": "Person with no Twitter details"},
            {
                "attr": "screen_name_and_user_id",
                "name": "Someone with a Twitter screen name and user ID",
                "user_id": "765",
                "screen_name": "notatwitteraccounteither",
            },
        ]:
            person = PersonFactory.create(name=person_details["name"])
            setattr(self, person_details["attr"], person)

            person.tmp_person_identifiers.create(
                internal_identifier=person_details.get("user_id", None),
                value_type="twitter_username",
                value=person_details.get("screen_name", ""),
            )

    @override_settings(TWITTER_APP_ONLY_BEARER_TOKEN="madeuptoken")
    def test_commmand_verbose_output(self, mock_requests):

        mock_requests.post.side_effect = fake_post_for_username_updater

        with capture_output() as (out, err):
            call_command("twitterbot_update_usernames", verbosity=3)

        self.assertEqual(
            split_output(out),
            [
                "Person with just a Twitter screen name has Twitter screen name (notreallyatwitteraccount) but no user ID",
                "Adding the user ID 321",
                "Person with just a Twitter user ID has a Twitter user ID: 987",
                "Correcting the screen name from None to ascreennamewewereunawareof",
                "Person with no Twitter details had no Twitter account information",
                "Someone with a Twitter screen name and user ID has a Twitter user ID: 765",
                "The screen name (notatwitteraccounteither) was already correct",
            ],
        )

    @override_settings(TWITTER_APP_ONLY_BEARER_TOKEN="madeuptoken")
    def test_commmand_adds_screen_name(self, mock_requests):

        mock_requests.post.side_effect = fake_post_for_username_updater

        with capture_output() as (out, err):
            call_command("twitterbot_update_usernames")

        self.assertEqual(
            self.just_userid.get_single_identifier_of_type(
                value_type="twitter_username"
            ),
            "ascreennamewewereunawareof",
        )

        self.assertEqual(
            split_output(out),
            [
                "Adding the user ID 321",
                "Correcting the screen name from None to ascreennamewewereunawareof",
            ],
        )

    @override_settings(TWITTER_APP_ONLY_BEARER_TOKEN="madeuptoken")
    def test_commmand_adds_user_id(self, mock_requests):

        mock_requests.post.side_effect = fake_post_for_username_updater

        with capture_output() as (out, err):
            call_command("twitterbot_update_usernames")

        self.assertEqual(
            self.just_screen_name.identifiers.get(scheme="twitter").identifier,
            "321",
        )

        self.assertEqual(
            split_output(out),
            [
                "Adding the user ID 321",
                "Correcting the screen name from None to ascreennamewewereunawareof",
            ],
        )

    @override_settings(TWITTER_APP_ONLY_BEARER_TOKEN="madeuptoken")
    def test_commmand_screen_name_was_wrong(self, mock_requests):
        def fake_post_screen_name_wrong(*args, **kwargs):
            data = kwargs["data"]
            mock_result = Mock()
            if "screen_name" in data:
                if (
                    data["screen_name"]
                    == "notatwitteraccounteither,notreallyatwitteraccount"
                ):
                    mock_result.json.return_value = [
                        {
                            "id": 321,
                            "screen_name": "notreallyatwitteraccount",
                            "profile_image_url_https": "https://example.com/a.jpg",
                        }
                    ]
                    return mock_result
            if "user_id" in data:
                if data["user_id"] == "765,987":
                    mock_result.json.return_value = [
                        {
                            "id": 987,
                            "screen_name": "ascreennamewewereunawareof",
                            "profile_image_url_https": "https://example.com/c.jpg",
                        },
                        {
                            "id": 765,
                            "screen_name": "changedscreenname",
                            "profile_image_url_https": "https://example.com/b.jpg",
                        },
                    ]
                    return mock_result
            raise Exception(
                "No Twitter API stub for {} {}".format(args, kwargs)
            )

        mock_requests.post.side_effect = fake_post_screen_name_wrong

        with capture_output() as (out, err):
            call_command("twitterbot_update_usernames")

        self.assertEqual(
            self.screen_name_and_user_id.get_single_identifier_of_type(
                "twitter_username"
            ),
            "changedscreenname",
        )

        self.assertEqual(
            split_output(out),
            [
                "Adding the user ID 321",
                "Correcting the screen name from None to ascreennamewewereunawareof",
                "Correcting the screen name from notatwitteraccounteither to changedscreenname",
            ],
        )

    @override_settings(TWITTER_APP_ONLY_BEARER_TOKEN="madeuptoken")
    def test_commmand_screen_name_disappeared(self, mock_requests):
        def fake_post_screen_name_disappeared(*args, **kwargs):
            data = kwargs["data"]
            mock_result = Mock()
            if "screen_name" in data:
                if (
                    data["screen_name"]
                    == "notatwitteraccounteither,notreallyatwitteraccount"
                ):
                    mock_result.json.return_value = [
                        {
                            "id": 765,
                            "screen_name": "notatwitteraccounteither",
                            "profile_image_url_https": "https://example.com/b.jpg",
                        }
                    ]
                    return mock_result
            if "user_id" in data:
                if data["user_id"] == "987":
                    mock_result.json.return_value = [
                        {
                            "id": 987,
                            "screen_name": "ascreennamewewereunawareof",
                            "profile_image_url_https": "https://example.com/c.jpg",
                        }
                    ]
                    return mock_result
            raise Exception(
                "No Twitter API stub for {} {}".format(args, kwargs)
            )

        mock_requests.post.side_effect = fake_post_screen_name_disappeared

        with capture_output() as (out, err):
            call_command("twitterbot_update_usernames")

        self.assertEqual(self.just_screen_name.get_twitter_username, "")
        self.assertEqual(
            self.just_screen_name.identifiers.filter(scheme="twitter").count(),
            0,
        )

        self.assertEqual(
            split_output(out),
            [
                "Removing screen name notreallyatwitteraccount for Person "
                "with just a Twitter screen name as it is not a valid "
                "Twitter screen name. "
                "/person/{}/person-with-just-a-twitter-screen-name".format(
                    self.just_screen_name.id
                ),
                "Correcting the screen name from None to ascreennamewewereunawareof",
            ],
        )

    @override_settings(TWITTER_APP_ONLY_BEARER_TOKEN="madeuptoken")
    def test_commmand_user_id_disappeared(self, mock_requests):
        def fake_post_user_id_disappeared(*args, **kwargs):
            data = kwargs["data"]
            mock_result = Mock()
            if "screen_name" in data:
                if (
                    data["screen_name"]
                    == "notatwitteraccounteither,notreallyatwitteraccount"
                ):
                    mock_result.json.return_value = [
                        {
                            "id": 321,
                            "screen_name": "notreallyatwitteraccount",
                            "profile_image_url_https": "https://example.com/a.jpg",
                        }
                    ]
                    return mock_result
            if "user_id" in data:
                if data["user_id"] == "765,987":
                    mock_result.json.return_value = {
                        "errors": [
                            {
                                "code": 17,
                                "message": "No user matches for specified terms.",
                            }
                        ]
                    }
                    return mock_result
            raise Exception(
                "No Twitter API stub for {} {}".format(args, kwargs)
            )

        mock_requests.post.side_effect = fake_post_user_id_disappeared

        self.assertEqual(
            self.screen_name_and_user_id.get_twitter_username,
            "notatwitteraccounteither",
        )
        with capture_output() as (out, err):
            call_command("twitterbot_update_usernames")

        self.assertIsNone(self.just_userid.get_twitter_username)
        self.assertEqual(
            self.just_userid.identifiers.filter(scheme="twitter").count(), 0
        )

        # Clear the cached_property for this object
        del self.screen_name_and_user_id.get_all_idenfitiers
        self.assertIsNone(self.screen_name_and_user_id.get_twitter_username)
        self.assertEqual(
            self.screen_name_and_user_id.identifiers.filter(
                scheme="twitter"
            ).count(),
            0,
        )

        self.assertEqual(
            split_output(out),
            [
                "Adding the user ID 321",
                "Removing user ID 987 for Person with just a Twitter user ID "
                "as it is not a valid Twitter user ID. "
                "/person/{}/person-with-just-a-twitter-user-id".format(
                    self.just_userid.id
                ),
                "Removing user ID 765 for Someone with a Twitter screen name "
                "and user ID as it is not a valid Twitter user ID. "
                "/person/{}/someone-with-a-twitter-screen-name-and-user-id".format(
                    self.screen_name_and_user_id.id
                ),
            ],
        )
