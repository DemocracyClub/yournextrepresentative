import people.tests.factories
from candidates.models import LoggedAction
from candidates.models.db import ActionType
from candidates.models.popolo_extra import Ballot
from candidates.tests.auth import TestUserMixin
from candidates.tests.test_models import BallotsWithResultsMixin
from django.test import TestCase
from elections.filters import region_choices
from elections.uk.templatetags.home_page_tags import results_progress_by_value


class TestResultsProgress(BallotsWithResultsMixin, TestCase):
    def test_for_regions(self):
        # create 10 ballots for each region without any results
        for code, label in region_choices():
            tags = {"NUTS1": {"key": code, "value": label}}
            self.create_ballots_with_results(num=10, tags=tags)

        # create 5 ballots for each region WITH results
        for code, label in region_choices():
            tags = {"NUTS1": {"key": code, "value": label}}
            self.create_ballots_with_results(num=4, resultset=True, tags=tags)

        # create 1 ballots for each region with only elected candidate
        for code, label in region_choices():
            tags = {"NUTS1": {"key": code, "value": label}}
            self.create_ballots_with_results(
                num=1, resultset=False, elected=True, tags=tags
            )

        result = results_progress_by_value(
            base_qs=Ballot.objects.all(),
            lookup_value="tags__NUTS1__key",
            label_field="tags__NUTS1__value",
        )
        # build how we expect
        expected = {}
        for code, label in region_choices():
            expected[code] = {
                "tags__NUTS1__key": code,
                "tags__NUTS1__value": label,
                "count": 15,
                "results_count": 5,
                "label": label,
                "posts_total": 15,
                "has_results": 5,
                "has_results_percent": 33,
            }
        self.assertEqual(result, expected)


class TestRecentChangesHomePageBlock(TestUserMixin, TestCase):
    def test_deleted_person_doesnt_break_homepage(self):
        """
        Regression test to ensure that deleting a person
        with recent LoggedActions doesn't break anything
        """

        test_person_1 = people.tests.factories.PersonFactory.create(
            id=9876, name="Test Candidate for Recent Changes"
        )
        LoggedAction.objects.create(
            user=self.user,
            action_type=ActionType.PERSON_CREATE,
            ip_address="127.0.0.1",
            person=test_person_1,
            popit_person_new_version="1234567890abcdef",
            source="Just for tests...",
        )
        self.action2 = LoggedAction.objects.create(
            user=self.user,
            action_type=ActionType.CANDIDACY_DELETE,
            ip_address="127.0.0.1",
            person=test_person_1,
            popit_person_new_version="987654321",
            source="Also just for testing",
        )

        # Deleting a person should null out the person ID on the
        # LoggedActions, not delete them.
        test_person_1.delete()
        resp = self.client.get("/")
        self.assertEqual(resp.status_code, 200)
