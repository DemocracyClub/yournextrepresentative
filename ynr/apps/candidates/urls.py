import candidates.views as views
from django.conf import settings
from django.urls import include, re_path
from django.views.generic import TemplateView
from django.views.generic.base import RedirectView

from .feeds import NeedsReviewFeed, RecentChangesFeed

urlpatterns = [
    re_path(
        r"^api-auth/",
        include("rest_framework.urls", namespace="rest_framework"),
    ),
    re_path(r"^", include(settings.ELECTION_APP_FULLY_QUALIFIED + ".urls")),
    re_path(
        r"^election/(?P<ballot_paper_id>[^/]+)/record-winner$",
        views.ConstituencyRecordWinnerView.as_view(),
        name="record-winner",
    ),
    re_path(
        r"^election/(?P<ballot_paper_id>[^/]+)/retract-winner$",
        views.ConstituencyRetractWinnerView.as_view(),
        name="retract-winner",
    ),
    re_path(  # Rename to CandidacyCreateView
        r"^election/(?P<ballot_paper_id>[^/]+)/candidacy$",
        views.CandidacyView.as_view(),
        name="candidacy-create",
    ),
    re_path(
        r"^election/(?P<ballot_paper_id>[^/]+)/candidacy/delete$",
        views.CandidacyDeleteView.as_view(),
        name="candidacy-delete",
    ),
    re_path(
        r"^election/(?P<ballot_paper_id>[^/]+)/person/create/$",
        views.NewPersonView.as_view(),
        name="person-create",
    ),
    re_path(
        r"^update-disallowed$",
        TemplateView.as_view(template_name="candidates/update-disallowed.html"),
        name="update-disallowed",
    ),
    # General views across the site (move to a "core" type app?)
    re_path(
        r"^all-edits-disallowed$",
        TemplateView.as_view(
            template_name="candidates/all-edits-disallowed.html"
        ),
        name="all-edits-disallowed",
    ),
    re_path(
        r"^recent-changes$",
        views.RecentChangesView.as_view(),
        name="recent-changes",
    ),
    re_path(
        r"^leaderboard$", views.LeaderboardView.as_view(), name="leaderboard"
    ),
    re_path(
        r"^leaderboard/contributions.csv$",
        views.UserContributions.as_view(),
        name="user-contributions",
    ),
    re_path(r"^feeds/changes.xml$", RecentChangesFeed(), name="changes_feed"),
    re_path(
        r"^feeds/needs-review.xml$", NeedsReviewFeed(), name="needs-review_feed"
    ),
    re_path(
        r"^help/api$",
        RedirectView.as_view(url="/api/", permanent=True),
        name="help-api",
    ),
    re_path(
        r"^help/results$", views.HelpResultsView.as_view(), name="help-results"
    ),
    re_path(r"^help/about$", views.HelpAboutView.as_view(), name="help-about"),
    re_path(
        r"^help/privacy$",
        RedirectView.as_view(
            url="https://democracyclub.org.uk/privacy/", permanent=True
        ),
        name="help-privacy",
    ),
    re_path(
        r"^help/photo-policy$",
        TemplateView.as_view(template_name="candidates/photo-policy.html"),
        name="help-photo-policy",
    ),
    # ----------------- Legacy redirect views
    re_path(
        r"^areas/(?P<type_and_area_ids>.*?)(?:/(?P<ignored_slug>.*))?$",
        views.AreasView.as_view(),
        name="areas-view",
    ),
    re_path(
        r"^posts-of-type/(?P<post_type>.*?)(?:/(?P<ignored_slug>.*))?$",
        views.PostsOfTypeView.as_view(),
        name="posts-of-type-view",
    ),
]

urlpatterns += [
    re_path(r"^numbers/", include("cached_counts.urls")),
    re_path(r"^moderation/", include("moderation_queue.urls")),
]
