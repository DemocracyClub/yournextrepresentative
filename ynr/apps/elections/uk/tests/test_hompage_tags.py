from django.test import TestCase
from candidates.models.popolo_extra import Ballot

from candidates.tests.test_models import BallotsWithResultsMixin
from elections.filters import region_choices
from elections.uk.templatetags.home_page_tags import results_progress_by_value


class TestResultsProgress(BallotsWithResultsMixin, TestCase):
    def test_for_regions(self):
        values = ["tags__NUTS1__key", "tags__NUTS1__value"]
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
