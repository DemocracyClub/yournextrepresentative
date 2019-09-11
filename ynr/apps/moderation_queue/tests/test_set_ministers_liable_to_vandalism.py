import mock

from django.core.management import call_command
from django.test import TestCase
from people.tests.factories import PersonFactory
from people.models import EditLimitationStatuses


class TestPersonUpdate(TestCase):
    @mock.patch(
        "moderation_queue.management.commands.moderation_queue_set_ministers_liable_to_vandalism.requests.get"
    )
    def test_management_command_sets_needs_review_flag(self, fake_get):
        fake_get.return_value.status_code = 200
        fake_get.return_value.json.return_value = {
            "memberships": [
                {
                    "id": "uk.parliament.data/Member/374/GovernmentPost/56",
                    "source": "datadotparl/governmentpost",
                    "role": "Deputy Prime Minister and First Secretary of State",
                    "person_id": "uk.org.publicwhip/person/10488",
                    "organization_id": "house-of-commons",
                    "start_date": "2001-06-08",
                    "end_date": "9999-12-30",
                }
            ]
        }
        person = PersonFactory(id=999)

        person.tmp_person_identifiers.create(
            internal_identifier="uk.org.publicwhip/person/10488",
            value_type="theyworkforyou",
        )
        person.save()

        cmd = call_command("moderation_queue_set_ministers_liable_to_vandalism")
        person.refresh_from_db()
        self.assertEqual(
            person.edit_limitations, EditLimitationStatuses.NEEDS_REVIEW.name
        )
