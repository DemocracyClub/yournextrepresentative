from typing import List, Optional, Tuple

import django_filters
from django.db.models import CharField, F, Q, Value
from django.db.models.functions import Cast, Concat
from elections.filters import DSLinkWidget, region_choices
from parties.models import Party

from .csv_fields import CSVField
from .models import MaterializedMemberships

BY_ELECTION_CHOICES = {
    ("True", "Only by-elections"),
    ("False", "Exclude by-elections"),
}

ELECTED_CHOICES = {
    ("True", "Elected"),
    ("False", "Not elected"),
}
CANCELLED_CHOICES = {
    ("True", "Cancelled"),
    ("False", "Not cancelled"),
}

LOCKED_CHOICES = {
    ("True", "Locked"),
    ("False", "Unlocked"),
}


class BallotPaperText(django_filters.CharFilter):
    field_name = "ballot_paper_id"

    def filter(self, qs, value):
        if value:
            qs = qs.filter(ballot_paper__ballot_paper_id__iregex=value)
        return qs


class ElectionIDText(django_filters.CharFilter):
    field_name = "election_id"

    def filter(self, qs, value):
        if value:
            qs = qs.filter(ballot_paper__election__slug__iregex=value)
        return qs


class DateIncludingReplacedFilter(django_filters.CharFilter):
    def filter(self, qs, value):
        if value:
            qs = qs.filter(
                Q(election_date=value)
                | Q(ballot_paper__replaces__ballot_paper_id__contains=value)
            )
        return qs


class MaterializedMembershipFilter(django_filters.FilterSet):
    by_election = django_filters.ChoiceFilter(
        field_name="is_by_election",
        label="Include by-elections?",
        lookup_expr="exact",
        choices=BY_ELECTION_CHOICES,
        empty_label="Yes",
        widget=DSLinkWidget(),
    )

    filter_by_region = django_filters.ChoiceFilter(
        widget=DSLinkWidget(),
        method="region_filter",
        label="Filter by region",
        choices=region_choices,
    )

    elected = django_filters.ChoiceFilter(
        field_name="elected",
        label="Elected",
        choices=ELECTED_CHOICES,
        empty_label="All Candidates",
        widget=DSLinkWidget(),
    )
    election_date = DateIncludingReplacedFilter(
        lookup_expr="regex",
        label="Election date",
        help_text="Blank fields will match anything",
    )

    ballot_paper_id = BallotPaperText(lookup_expr="regex")
    election_id = ElectionIDText(
        lookup_expr="regex",
        field_name="ballot_paper__election__slug",
        label="Election ID matches RegEx",
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
    cancelled = django_filters.ChoiceFilter(
        field_name="ballot_paper__cancelled", choices=CANCELLED_CHOICES
    )

    locked = django_filters.ChoiceFilter(
        field_name="ballot_paper__candidates_locked",
        empty_label="All",
        choices=LOCKED_CHOICES,
    )

    class Meta:
        model = MaterializedMemberships
        fields = [
            "by_election",
            "elected",
            "election_date",
            "ballot_paper_id",
            "election_id",
            "party_id",
        ]

    def region_filter(self, queryset, name, value):
        """
        Filter queryset by region using the NUTS1 code
        """
        return queryset.filter(ballot_paper__tags__NUTS1__key__in=[value])

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

    def filter_null_or_empty_int(self, queryset, name, value):
        annotation = {}
        annotation[f"{name}_filterfield"] = Cast(
            name, output_field=CharField(blank=True)
        )

        queryset = queryset.annotate(**annotation)
        if value == "yes":
            return queryset.filter(~Q(**{f"{name}_filterfield__exact": ""}))
        if value == "no":
            return queryset.filter(Q(**{f"{name}_filterfield__isnull": True}))
        return queryset


def create_materialized_membership_filter(
    fields: Optional[List[Tuple[str, CSVField]]] = None,
):
    """
    Needed for adding dynamic filters to the class in a thread-safe way.

    If we just add these to the class in an __init__ method, there is a chance that
    the class is re-used across different requests.

    Using a builder like this allows each request to have it's own class, making sure it's safe.

    :param fields:
    :return:
    """

    class DynamicMaterializedMembershipFilter(MaterializedMembershipFilter):
        ...

    for field_name, field in fields:
        if not field.dynamic_filter:
            continue
        method = "filter_null_or_empty_str"
        if field.value_type == "int":
            method = "filter_null_or_empty_int"

        DynamicMaterializedMembershipFilter.base_filters[
            f"has_{field_name}"
        ] = django_filters.ChoiceFilter(
            field_name=field_name,
            method=method,
            label=f"Has {field.label}",
            choices=[("yes", "Yes"), ("no", "No")],
            # widget=forms.CheckboxInput,
        )

    return DynamicMaterializedMembershipFilter
