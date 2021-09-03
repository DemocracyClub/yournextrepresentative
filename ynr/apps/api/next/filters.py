from django_filters import filterset, filters


class LastUpdatedFilter(filterset.FilterSet):
    last_updated = filters.IsoDateTimeFilter(
        field_name="modified",
        lookup_expr="gt",
        label="Last updated",
        help_text="An ISO datetime",
    )
