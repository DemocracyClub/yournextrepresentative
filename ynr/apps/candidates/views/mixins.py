from datetime import timedelta

from dateutil.parser import parse
from django.db.models import Count, F
from django.utils import timezone

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
            # (
            #     "May 2024 Elections",
            #     timezone.make_aware(parse("2024-03-01")),
            #     timezone.make_aware(parse("2024-05-31")),
            # ),
            (
                "Since the 4 July 2024 General Election Announcement",
                timezone.make_aware(parse("2024-05-22")),
                timezone.now(),
            ),
        ]
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
