from urllib.parse import urlencode

import django_filters
from django_filters.widgets import LinkWidget

from candidates.models import LoggedAction
from candidates.models.db import EditType
from moderation_queue.review_required_helper import REVIEW_TYPES


class LoggedActionAPIFilter(django_filters.FilterSet):
    class Meta:
        model = LoggedAction
        fields = ["action_type"]

    action_type = django_filters.AllValuesMultipleFilter(
        field_name="action_type"
    )


def get_action_types():
    return [
        (x, x)
        for x in LoggedAction.objects.all()
        .values_list("action_type", flat=True)
        .distinct()
    ]


class LoggedActionRecentChangesFilter(django_filters.FilterSet):
    """
    For filtering the recent changes page
    """

    class Meta:
        model = LoggedAction
        fields = ["action_type", "flagged_type", "edit_type", "username"]

    flagged_type = django_filters.ChoiceFilter(
        choices=[
            (t.type, t.label)
            for t in REVIEW_TYPES
            if not t.type.startswith("no_review_")
        ],
        widget=LinkWidget(),
    )

    edit_type = django_filters.ChoiceFilter(
        choices=[(edit_type.name, edit_type.value) for edit_type in EditType],
        widget=LinkWidget(),
    )

    action_type = django_filters.AllValuesMultipleFilter(
        choices=get_action_types
    )

    username = django_filters.CharFilter(
        label="User name", method="filter_username"
    )

    def filter_username(self, queryset, name, value):
        return queryset.filter(user__username=value)


def recent_changes_filter_shortcuts(request):
    shortcut_list = [
        {
            "name": "humans_only",
            "label": "Humans only",
            "query": {"edit_type": "USER"},
        }
    ]

    query = dict(request.GET)
    shortcuts = {"list": shortcut_list}
    for shortcut in shortcuts["list"]:
        shortcut["querystring"] = urlencode(shortcut["query"], doseq=True)
        if shortcut["query"] == query:
            shortcut["active"] = True
            shortcuts["active"] = shortcut
    return shortcuts
