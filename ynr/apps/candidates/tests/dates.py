import copy
from datetime import date, timedelta, datetime, time
from django.utils import timezone

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


def mock_in_past():
    return timezone.make_aware(datetime(2019, 1, 1, 10, 10, 10))


def mock_on_election_day(election):
    return timezone.make_aware(
        datetime.combine(election.election_date, time(10, 10, 10))
    )


def mock_on_election_day_polls_closed(election):
    return timezone.make_aware(
        datetime.combine(election.election_date, time(23, 10, 10))
    )


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
