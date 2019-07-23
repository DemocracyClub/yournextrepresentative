import copy
from datetime import date, timedelta

from django.conf import settings

date_in_near_future = date.today() + timedelta(days=14)
date_in_near_past = date.today() - timedelta(days=14)

FOUR_YEARS_IN_DAYS = 1462

election_date_before = lambda r: {"DATE_TODAY": date.today()}
election_date_on_election_day = lambda r: {"DATE_TODAY": date_in_near_future}
election_date_after = lambda r: {
    "DATE_TODAY": date.today() + timedelta(days=28)
}

default_templates = settings.TEMPLATES


def _insert_context_processor(path):
    templates = copy.deepcopy(default_templates)
    cps = list(templates[0]["OPTIONS"]["context_processors"])
    cps.append(path)
    templates[0]["OPTIONS"]["context_processors"] = cps
    return templates


templates_before = _insert_context_processor(
    "candidates.tests.dates.election_date_before"
)
templates_on_election_day = _insert_context_processor(
    "candidates.tests.dates.election_date_on_election_day"
)
templates_after = _insert_context_processor(
    "candidates.tests.dates.election_date_after"
)
