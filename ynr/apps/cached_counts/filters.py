import django_filters
from data_exports.filters import BallotPaperText
from django import forms
from django.db.models import CharField, F, Q, Value
from django.db.models.functions import Cast, Concat
from elections.filters import DSLinkWidget, region_choices
from parties.models import Party
from ynr_refactoring.settings import PersonIdentifierFields


class CompletenessFilter(django_filters.FilterSet):
    def __init__(self, data=None, queryset=None, *, request=None, prefix=None):
        for identifier in PersonIdentifierFields:
            self.base_filters[
                f"has_{identifier.name}"
            ] = django_filters.ChoiceFilter(
                field_name=identifier.name,
                method="filter_null_or_empty_str",
                label=f"Has {identifier.value}",
                choices=[("yes", "Yes"), ("no", "No")],
                widget=forms.HiddenInput,
            )

        super().__init__(data, queryset, request=request, prefix=prefix)

    ballot_paper_id = BallotPaperText(lookup_expr="regex")
    filter_by_region = django_filters.ChoiceFilter(
        widget=DSLinkWidget(),
        method="region_filter",
        label="Filter by region",
        choices=region_choices,
    )

    party_id = django_filters.MultipleChoiceFilter(
        field_name="party_id",
        choices=Party.objects.annotate(
            label=Concat(
                F("name"),
                Value(" ("),
                F("ec_id"),
                Value(", "),
                F("register"),
                Value(")"),
                output_field=CharField(),
            )
        ).values_list("ec_id", "label"),
    )

    def region_filter(self, queryset, name, value):
        """
        Filter queryset by region using the NUTS1 code
        """
        return queryset.filter(ballot_paper__tags__NUTS1__key=value)

    def filter_null_or_empty_str(self, queryset, name, value):
        annotation = {}
        annotation[f"{name}_filterfield"] = Cast(
            name, output_field=CharField(blank=True)
        )

        queryset = queryset.annotate(**annotation)
        if value == "yes":
            return queryset.filter(~Q(**{f"{name}_filterfield__exact": ""}))
        if value == "no":
            return queryset.filter(
                Q(**{f"{name}__exact": ""})
                | Q(**{f"{name}_filterfield__isnull": True})
            )
        return queryset
