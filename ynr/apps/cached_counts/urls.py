from django.urls import re_path

from .views import (
    AttentionNeededView,
    CandidateCompletenessView,
    ConstituencyCountsView,
    ElectionReportView,
    PartyCountsView,
    ReportsHomeView,
)

urlpatterns = [
    re_path(r"^$", ReportsHomeView.as_view(), name="reports_home"),
    re_path(
        r"^attention-needed$",
        AttentionNeededView.as_view(),
        name="attention_needed",
    ),
    re_path(
        r"^election/(?P<election>[-\w\.0-9]+)/parties$",
        PartyCountsView.as_view(),
        name="parties_counts",
    ),
    re_path(
        r"^election/(?P<election>[-\w\.0-9]+)/posts$",
        ConstituencyCountsView.as_view(),
        name="posts_counts",
    ),
    re_path(
        r"^election/(?P<election>[-\w\.0-9]+)/completeness$",
        CandidateCompletenessView.as_view(),
        name="candidate_completeness",
    ),
    re_path(
        r"^report/(?P<report_slug>[-\w\.0-9]+)/$",
        ElectionReportView.as_view(),
        name="election_report_view",
    ),
]
