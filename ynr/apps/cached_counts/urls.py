from django.urls import re_path

from .views import (
    AttentionNeededView,
    ConstituencyCountsView,
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
]
