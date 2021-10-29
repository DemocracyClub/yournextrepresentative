from urllib.parse import urlencode

import django_filters

from candidates.models import LoggedAction
from candidates.models.db import ActionType, EditType
from elections.filters import DSLinkWidget
from moderation_queue.review_required_helper import REVIEW_TYPES


def get_action_types():
    return ActionType.choices


class LoggedActionAPIFilter(django_filters.FilterSet):

    created = django_filters.DateFilter(lookup_expr="gte")

    class Meta:
        model = LoggedAction
        fields = ["action_type", "created"]

    action_type = django_filters.MultipleChoiceFilter(choices=get_action_types)


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
        widget=DSLinkWidget(),
    )

    edit_type = django_filters.ChoiceFilter(
        choices=[(edit_type.name, edit_type.value) for edit_type in EditType],
        widget=DSLinkWidget(),
    )

    action_type = django_filters.MultipleChoiceFilter(choices=get_action_types)

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
