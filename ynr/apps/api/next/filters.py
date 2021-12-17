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


class UncontestedMixin(filterset.FilterSet):
    uncontested = filters.BooleanFilter(
        field_name="uncontested",
        lookup_expr="gt",
        label="Uncontested",
        help_text="Uncontested ballots",
        method="filter_uncontested",
    )

    def filter_uncontested(self, queryset, name, value):
        """
        Default method that can be overided to check additional fields in subclass
        """
        name = f"{name}__gt"
        return queryset.filter(**{name: value})
