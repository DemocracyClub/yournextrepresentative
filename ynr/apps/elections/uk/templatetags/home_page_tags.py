from candidates.models import Ballot
from django import template
from django.conf import settings
from django.db.models import Count, F, Func, Q, Sum, TextField, Value
from elections.filters import filter_shortcuts
from elections.models import Election
from popolo.models import Membership

register = template.Library()


def sopn_progress_by_election_slug_prefix(self, election_slug_prefix):
    election_qs = Election.objects.filter(slug__startswith=election_slug_prefix)
    return self.sopn_progress_by_election(election_qs)


def results_progress_by_value(base_qs, lookup_value, label_field=None):
    values = [lookup_value]

    if label_field:
        values.append(label_field)

    ballot_qs = base_qs.values(*values).distinct()
    ballot_qs = ballot_qs.annotate(
        count=Count("ballot_paper_id", distinct=True)
    )
    results_filter = Q(resultset__isnull=False) | Q(membership__elected__gte=1)
    ballot_qs = ballot_qs.annotate(
        results_count=Count(
            "ballot_paper_id", distinct=True, filter=results_filter
        )
    ).order_by(lookup_value)
    values_dict = {}

    for row in ballot_qs:
        if label_field:
            row["label"] = row.get(label_field)
            if not row["label"]:
                continue
        row["posts_total"] = row["count"] or 0
        row["has_results"] = row["results_count"] or 0
        row["has_results_percent"] = round(
            float(row["has_results"]) / float(row["count"]) * 100
        )
        values_dict[str(row[lookup_value])] = row

    return values_dict


def sopn_progress_by_value(base_qs, lookup_value, label_field=None):
    values = [lookup_value]

    if label_field:
        values.append(label_field)

    ballot_qs = base_qs.values(*values).distinct()
    ballot_qs = ballot_qs.annotate(
        has_sopn_count=Count("pk", filter=Q(sopn__isnull=False), distinct=True),
        locked_count=Count(
            "pk", filter=Q(candidates_locked=True), distinct=True
        ),
        locksuggested_count=Count("suggestedpostlock", distinct=True),
        count=Count("ballot_paper_id", distinct=True),
    ).order_by(lookup_value)
    values_dict = {}

    for row in ballot_qs:
        if label_field:
            row["label"] = row.get(label_field)
            if not row["label"]:
                continue
        row["posts_total"] = row["count"] or 0
        row["sopns_imported"] = row["has_sopn_count"] or 0
        row["sopns_imported_percent"] = round(
            float(row["sopns_imported"]) / float(row["posts_total"]) * 100
        )

        row["posts_locked"] = row["locked_count"] or 0
        row["posts_locked_percent"] = round(
            float(row["posts_locked"]) / float(row["posts_total"]) * 100
        )
        row["posts_lock_suggested"] = min(
            (row["locksuggested_count"] or 0) + row["posts_locked"],
            row["posts_total"],
        )
        row["posts_locked_suggested_percent"] = round(
            float(row["posts_lock_suggested"]) / float(row["posts_total"]) * 100
        )
        values_dict[str(row[lookup_value])] = row

    return values_dict


@register.inclusion_tag(
    "includes/sopn_import_progress.html", takes_context=True
)
def sopn_import_progress(context):
    context["SHOW_SOPN_TRACKER"] = (
        getattr(settings, "FRONT_PAGE_CTA", False) == "SOPN_TRACKER"
    )
    context["SOPN_SHEET_URL"] = getattr(settings, "SOPN_SHEET_URL", None)
    context["SOPN_DATES"] = getattr(settings, "SOPN_DATES", None)
    if context["SHOW_SOPN_TRACKER"]:
        context["sopn_tracker_election_name"] = settings.SOPN_TRACKER_INFO[
            "election_name"
        ]

        value = settings.SOPN_TRACKER_INFO["election_date"]

        base_ballot_qs = Ballot.objects.filter(election__election_date=value)
        # TMP for UK general
        base_ballot_qs = base_ballot_qs.filter(
            ballot_paper_id__startswith="parl."
        )
        context["sopn_progress"] = sopn_progress_by_value(
            base_ballot_qs, lookup_value="election__election_date"
        )[value]

        context["sopn_progress_by_region"] = sopn_progress_by_value(
            base_ballot_qs,
            lookup_value="tags__NUTS1__key",
            label_field="tags__NUTS1__value",
        )
        election_type = Func(
            F("election__slug"),
            Value("."),
            Value(1),
            function="split_part",
            output_field=TextField(),
        )
        context["sopn_progress_by_election_type"] = sopn_progress_by_value(
            base_ballot_qs.annotate(election_type=election_type),
            lookup_value="election_type",
            label_field="election__for_post_role",
        )

    return context


@register.inclusion_tag("includes/election_stats.html", takes_context=True)
def current_election_stats(context):
    context["SHOW_ELECTION_STATS"] = (
        getattr(settings, "FRONT_PAGE_CTA", False) == "ELECTION_STATS"
    )

    if context["SHOW_ELECTION_STATS"]:
        context["election_name"] = settings.SOPN_TRACKER_INFO["election_name"]
        election_date = settings.SOPN_TRACKER_INFO["election_date"]
        election_qs = Election.objects.filter(election_date=election_date)

        stats = {
            "elections": election_qs.count(),
            "seats_contested": Ballot.objects.filter(
                election__in=election_qs
            ).aggregate(count=Sum("winner_count"))["count"],
            "candidates": Membership.objects.filter(
                ballot__election__in=election_qs
            ).count(),
        }
        context["election_stats"] = stats

    return context


@register.inclusion_tag("includes/results_progress.html", takes_context=True)
def results_progress(context):
    context["SHOW_RESULTS_PROGRESS"] = (
        getattr(settings, "FRONT_PAGE_CTA", False) == "RESULTS_PROGRESS"
    )

    if context["SHOW_RESULTS_PROGRESS"]:
        election_date = settings.SOPN_TRACKER_INFO["election_date"]

        context["election_name"] = settings.SOPN_TRACKER_INFO["election_name"]
        ballot_qs = Ballot.objects.filter(
            election__election_date=election_date,
            cancelled=False,
            election__slug="parl.2024-07-04",
        )

        context["results_entered"] = ballot_qs.has_results().count()
        context["areas_total"] = ballot_qs.count()
        try:
            context["results_percent"] = round(
                float(context["results_entered"])
                / float(context["areas_total"])
                * 100
            )
        except ZeroDivisionError:
            context["results_percent"] = 0

        context["results_progress_by_region"] = results_progress_by_value(
            ballot_qs,
            lookup_value="tags__NUTS1__key",
            label_field="tags__NUTS1__value",
        )

        election_type = Func(
            F("election__slug"),
            Value("."),
            Value(1),
            function="split_part",
            output_field=TextField(),
        )

        context[
            "results_progress_by_election_type"
        ] = results_progress_by_value(
            ballot_qs.annotate(election_type=election_type),
            lookup_value="election_type",
            label_field="election__for_post_role",
        )

    shortcuts = filter_shortcuts(context["request"])["list"]
    context["has_results_shortcut"] = [
        shortcut for shortcut in shortcuts if shortcut["name"] == "has_results"
    ][0]

    return context


@register.inclusion_tag("includes/by-election-ctas.html", takes_context=True)
def by_election_ctas(context):
    context["SHOW_BY_ELECTION_CTA"] = (
        getattr(settings, "FRONT_PAGE_CTA", False) == "BY_ELECTIONS"
    )

    if context["SHOW_BY_ELECTION_CTA"]:
        dates_to_ignore = getattr(settings, "SCHEDULED_ELECTION_DATES", [])

        all_ballots = (
            Ballot.objects.filter(
                election__current=True, ballot_paper_id__contains=".by."
            )
            .exclude(election__election_date__in=dates_to_ignore)
            .order_by("election__election_date", "election")
            .select_related("election", "post")
            .prefetch_related("membership_set")
        )
        context["upcoming_ballots"] = [
            ballot for ballot in all_ballots if not ballot.election.in_past
        ]
        context["past_ballots"] = [
            ballot for ballot in all_ballots if ballot.election.in_past
        ]
    return context


@register.inclusion_tag("includes/data_download.html", takes_context=True)
def data_download(context):
    context["DATA_DOWNLOAD"] = (
        getattr(settings, "FRONT_PAGE_CTA", False) == "DATA_DOWNLOAD"
    )

    if context["DATA_DOWNLOAD"]:
        context["election_date"] = settings.DATA_DOWNLOAD_INFO["election_date"]
        context["election_regex"] = settings.DATA_DOWNLOAD_INFO[
            "election_regex"
        ]
        context["election_name"] = settings.DATA_DOWNLOAD_INFO["election_name"]
    return context


@register.inclusion_tag("includes/results_download.html", takes_context=True)
def results_download(context):
    context["RESULTS_DOWNLOAD"] = (
        getattr(settings, "FRONT_PAGE_CTA", False) == "RESULTS_DOWNLOAD"
    )

    if context["RESULTS_DOWNLOAD"]:
        context["election_date"] = settings.RESULTS_DOWNLOAD_INFO[
            "election_date"
        ]
        context["election_regex"] = settings.RESULTS_DOWNLOAD_INFO[
            "election_regex"
        ]
        context["election_name"] = settings.RESULTS_DOWNLOAD_INFO[
            "election_name"
        ]
    return context
