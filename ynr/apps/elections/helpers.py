import datetime
from functools import update_wrapper
from typing import List, Optional

from candidates.models import Ballot
from django.core.cache import cache
from django.db.models import Count
from django.utils import timezone


class ElectionIDSwitcher:
    def __init__(self, ballot_view, election_view, **initkwargs):
        self.election_id_kwarg = initkwargs.get("election_id_kwarg", "election")
        self.ballot_view = ballot_view
        self.election_view = election_view

    def __call__(self, request, *args, **kwargs):
        ballot_qs = Ballot.objects.filter(
            ballot_paper_id=kwargs[self.election_id_kwarg]
        )

        if ballot_qs.exists():
            # This is a ballot paper ID
            view_cls = self.ballot_view
        else:
            # Assume this is an election ID, or let the election_view
            # deal with the 404
            view_cls = self.election_view

        view = view_cls.as_view()

        view.view_class = view_cls
        # take name and docstring from class
        update_wrapper(view, view_cls, updated=())
        # and possible attributes set by decorators
        # like csrf_exempt from dispatch
        update_wrapper(view, view_cls.dispatch, assigned=())

        self.__name__ = self.__qualname__ = view.__name__
        return view(request, *args, **kwargs)


def four_weeks_before_election_date(election):
    """
    Takes an election object and a datetime object four weeks prior to the
    election date.
    Used in data migrations where we want to set a realistic created timestamp
    on old objects.
    """
    election_date = election.election_date - timezone.timedelta(weeks=4)
    return timezone.datetime(
        election_date.year,
        election_date.month,
        election_date.day,
        tzinfo=datetime.timezone.utc,
    )


def get_latest_charismatic_election_dates(count=5) -> List[datetime.date]:
    """
    Returns a list of dates that "charismatic" elections took place on.

    This is typically a scheduled election date (e.g May elections).

    Useful for presenting a list of major election dates.

    As the data doesn't change very much, we cache it and set a long TTL.

    """

    key = f"charismatic_election_dates-{count}"
    ttl = 60 * 60 * 24  # 1 day in seconds
    result = cache.get(key)

    if not result:
        result = list(
            Ballot.objects.exclude(ballot_paper_id__contains=".by.")
            .order_by("-election__election_date")
            .values("election__election_date")
            .annotate(ballots=Count("ballot_paper_id", distinct=True))
            .exclude(ballot_paper_id__startswith="local.city-of-london")
            .filter(replaces=None)
            .filter(ballots__gt=10)
            .values_list("election__election_date", flat=True)[:count]
        )

        cache.set(key, result, ttl)

    return result


def get_last_charismatic_election_date() -> Optional[datetime.date]:
    """
    Returns the first date that's in the past from
    `get_latest_charismatic_election_dates`

    """

    dates = get_latest_charismatic_election_dates()
    today = datetime.date.today()
    for date in dates:
        if date < today:
            return date
    return None
