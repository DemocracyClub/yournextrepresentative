import django_filters
from django_filters import BaseInFilter
from elections.filters import DSLinkWidget

from .models import MaterializedMemberships

BY_ELECTION_CHOICES = {
    ("True", "Only by-elections"),
    ("False", "Exclude by-elections"),
}

ELECTED_CHOICES = {
    ("True", "Elected"),
    ("False", "Not elected"),
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
