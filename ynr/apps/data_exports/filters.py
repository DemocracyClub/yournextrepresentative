from typing import List, Optional, Tuple

import django_filters
from django.db.models import CharField, Q
from django.db.models.functions import Cast
from django_filters import BaseInFilter
from elections.filters import DSLinkWidget

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


class PartyINFilter(BaseInFilter, django_filters.CharFilter):
    pass


class MaterializedMembershipFilter(django_filters.FilterSet):
    by_election = django_filters.ChoiceFilter(
        field_name="is_by_election",
        label="Include by-elections?",
        lookup_expr="exact",
        choices=BY_ELECTION_CHOICES,
        empty_label="Yes",
        widget=DSLinkWidget(),
    )

    elected = django_filters.ChoiceFilter(
        field_name="elected",
        label="Elected",
        choices=ELECTED_CHOICES,
        empty_label="All Candidates",
        widget=DSLinkWidget(),
    )
    election_date = django_filters.CharFilter(
        lookup_expr="regex",
    )

    ballot_paper_id = BallotPaperText(lookup_expr="regex")
    election_id = ElectionIDText(
        lookup_expr="regex",
        field_name="ballot_paper__election__slug",
        label="Election ID matches RegEx",
    )
    party_id = PartyINFilter(
        field_name="party_id",
    )
    cancelled = django_filters.ChoiceFilter(
        field_name="ballot_paper__cancelled", choices=CANCELLED_CHOICES
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
