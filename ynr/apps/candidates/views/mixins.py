from datetime import timedelta

from dateutil.parser import parse
from django.contrib.auth.models import User
from django.db.models import Count, F
from django.utils import timezone
from elections.helpers import get_latest_charismatic_election_dates

from ..models import LoggedAction


class ContributorsMixin(object):
    def get_leaderboards(self, all_time=True):
        result = []
        boards = [
            (
                "In the last week",
                timezone.now() - timedelta(days=7),
                timezone.now(),
            ),
        ]

        for date in get_latest_charismatic_election_dates(2):
            boards.append(
                (
                    date.strftime("%B %Y"),
                    date - timedelta(days=60),
                    date + timedelta(days=7),
                ),
            )

        if all_time:
            boards.insert(0, ("All Time", None, None))

        for title, since, until in boards:
            interesting_actions = LoggedAction.objects.exclude(
                action_type="set-candidate-not-elected"
            )

            if since:
                qs = interesting_actions.filter(created__gt=since)
            else:
                qs = interesting_actions

            if until:
                qs = qs.filter(created__lt=until)

            rows = (
                qs.annotate(username=F("user__username"))
                .values("username")
                .annotate(edit_count=Count("user"))
                .order_by("-edit_count")
            )

            leaderboard = {"title": title, "rows": rows[:25]}
            result.append(leaderboard)
        return result

    def get_recent_changes_queryset(self):
        return (
            LoggedAction.objects.exclude(
                action_type="set-candidate-not-elected"
            )
            .filter(user__isnull=False)
            .select_related("user", "person", "ballot", "ballot__post")
            .order_by("-created")
        )

    def get_num_new_users(self):
        """Return the number of new users
        created since the GE 2024 announcement."""
        return User.objects.filter(date_joined__gt=parse("2024-05-22")).count()  # noqa
