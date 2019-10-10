import django_filters

from candidates.models import LoggedAction


class LoggedActionAPIFilter(django_filters.FilterSet):
    class Meta:
        model = LoggedAction
        fields = ["action_type"]

    action_type = django_filters.AllValuesMultipleFilter(
        field_name="action_type"
    )
