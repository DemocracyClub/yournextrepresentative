from django_filters import filterset, filters


class LastUpdatedMixin(filterset.FilterSet):
    last_updated = filters.IsoDateTimeFilter(
        field_name="modified",
        lookup_expr="gt",
        label="Last updated",
        help_text="An ISO datetime",
        method="filter_last_updated",
    )

    def filter_last_updated(self, queryset, name, value):
        """
        Default method that can be overided to check additional fields in subclass
        """
        name = f"{name}__gt"
        return queryset.filter(**{name: value})
