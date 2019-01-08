from django.conf.urls import url

from ynr_refactoring import views


urlpatterns = [
    url(
        r"^election/(?P<election>[^/]+)/constituencies$",
        views.RedirectConstituencyListView.as_view(),
        name="constituencies_redirect",
    ),
    url(
        r"^posts$", views.RedirectPostsListView.as_view(), name="posts_redirect"
    ),
    url(
        r"^election/(?P<election>[^/]+)/constituencies/unlocked$",
        views.RedirectConstituenciesUnlockedView.as_view(),
        name="constituencies_unlocked_redirect",
    ),
    url(
        r"^election/(?P<election>[^/]+)/post/(?P<post_id>[^/]+)/(?P<ignored_slug>.*)$",
        views.RedirectConstituencyDetailView.as_view(),
        name="constituency_redirect",
    ),
    url(
        r"^election/(?P<election>[^/]+)/post/(?P<post_id>[^/]+)/(?P<ignored_slug>.*).csv$",
        views.RedirectConstituencyDetailCSVView.as_view(),
        name="constituency_csv_redirect",
    ),
]
