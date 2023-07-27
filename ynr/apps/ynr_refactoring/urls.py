from django.urls import re_path
from ynr_refactoring import views

urlpatterns = [
    re_path(
        r"^election/(?P<election>[^/]+)/constituencies$",
        views.RedirectConstituencyListView.as_view(),
        name="constituencies_redirect",
    ),
    re_path(
        r"^posts$", views.RedirectPostsListView.as_view(), name="posts_redirect"
    ),
    re_path(
        r"^election/(?P<election>[^/]+)/constituencies/unlocked$",
        views.RedirectConstituenciesUnlockedView.as_view(),
        name="constituencies_unlocked_redirect",
    ),
    re_path(
        r"^election/(?P<election>[^/]+)/post/(?P<post_id>[^/]+)/(?P<ignored_slug>[^.]+)$",
        views.RedirectConstituencyDetailView.as_view(),
        name="constituency_redirect",
    ),
    re_path(
        r"^election/(?P<election>[^/]+)/post/(?P<post_id>[^/]+)/$",
        views.RedirectConstituencyDetailView.as_view(),
    ),
    re_path(
        r"^election/(?P<election>[^/]+)/post/(?P<post_id>[^/]+)/(?P<ignored_slug>[^.]+).csv$",
        views.RedirectConstituencyDetailCSVView.as_view(),
        name="constituency_csv_redirect",
    ),
    re_path(
        r"^election/(?P<election>[^/]+)/party/(?P<legacy_slug>[^/]+)/(?P<ignored_slug>[^.]+)$",
        views.RedirectPartyDetailView.as_view(),
        name="party_redirect",
    ),
    re_path(
        r"^upload_document/(?P<document_id>[^/]+)/$",
        views.RedirectSOPNView.as_view(),
        name="sopn_redirect",
    ),
]
