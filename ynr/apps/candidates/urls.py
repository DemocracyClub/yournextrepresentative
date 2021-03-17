from django.conf import settings
from django.conf.urls import include, url
from django.views.decorators.cache import cache_page
from django.views.generic import TemplateView
from django.views.generic.base import RedirectView

import candidates.views as views

from .feeds import NeedsReviewFeed, RecentChangesFeed

urlpatterns = [
    url(
        r"^api-auth/",
        include("rest_framework.urls", namespace="rest_framework"),
    ),
    url(r"^", include(settings.ELECTION_APP_FULLY_QUALIFIED + ".urls")),
    url(
        r"^election/(?P<ballot_paper_id>[^/]+)/record-winner$",
        views.ConstituencyRecordWinnerView.as_view(),
        name="record-winner",
    ),
    url(
        r"^election/(?P<ballot_paper_id>[^/]+)/retract-winner$",
        views.ConstituencyRetractWinnerView.as_view(),
        name="retract-winner",
    ),
    url(  # Rename to CandidacyCreateView
        r"^election/(?P<ballot_paper_id>[^/]+)/candidacy$",
        views.CandidacyView.as_view(),
        name="candidacy-create",
    ),
    url(
        r"^election/(?P<ballot_paper_id>[^/]+)/candidacy/delete$",
        views.CandidacyDeleteView.as_view(),
        name="candidacy-delete",
    ),
    url(
        r"^election/(?P<election>[^/]+)/person/create/$",
        views.NewPersonView.as_view(),
        name="person-create",
    ),
    url(
        r"^update-disallowed$",
        TemplateView.as_view(template_name="candidates/update-disallowed.html"),
        name="update-disallowed",
    ),
    # General views across the site (move to a "core" type app?)
    url(
        r"^all-edits-disallowed$",
        TemplateView.as_view(
            template_name="candidates/all-edits-disallowed.html"
        ),
        name="all-edits-disallowed",
    ),
    url(
        r"^recent-changes$",
        views.RecentChangesView.as_view(),
        name="recent-changes",
    ),
    url(r"^leaderboard$", views.LeaderboardView.as_view(), name="leaderboard"),
    url(
        r"^leaderboard/contributions.csv$",
        views.UserContributions.as_view(),
        name="user-contributions",
    ),
    url(r"^feeds/changes.xml$", RecentChangesFeed(), name="changes_feed"),
    url(
        r"^feeds/needs-review.xml$", NeedsReviewFeed(), name="needs-review_feed"
    ),
    url(
        r"^help/api$",
        RedirectView.as_view(url="/api/", permanent=True),
        name="help-api",
    ),
    url(
        r"^help/results$", views.HelpResultsView.as_view(), name="help-results"
    ),
    url(r"^help/about$", views.HelpAboutView.as_view(), name="help-about"),
    url(
        r"^help/privacy$",
        RedirectView.as_view(
            url="https://democracyclub.org.uk/privacy/", permanent=True
        ),
        name="help-privacy",
    ),
    url(
        r"^help/photo-policy$",
        TemplateView.as_view(template_name="candidates/photo-policy.html"),
        name="help-photo-policy",
    ),
    url(
        r"^copyright-question$",
        views.AskForCopyrightAssigment.as_view(),
        name="ask-for-copyright-assignment",
    ),
    # ----------------- Legacy redirect views
    url(
        r"^areas/(?P<type_and_area_ids>.*?)(?:/(?P<ignored_slug>.*))?$",
        views.AreasView.as_view(),
        name="areas-view",
    ),
    url(
        r"^posts-of-type/(?P<post_type>.*?)(?:/(?P<ignored_slug>.*))?$",
        views.PostsOfTypeView.as_view(),
        name="posts-of-type-view",
    ),
    url(
        r"^person/(?P<person_id>\d+)/revert$",
        views.RevertPersonView.as_view(),
        name="person-revert",
    ),
    url(
        r"^person/(?P<person_id>\d+)/merge_conflict/(?P<other_person_id>\d+)/not_standing/$",
        views.CorrectNotStandingMergeView.as_view(),
        name="person-merge-correct-not-standing",
    ),
    url(
        r"^person/(?P<person_id>\d+)/merge$",
        views.MergePeopleView.as_view(),
        name="person-merge",
    ),
    url(
        r"^person/(?P<person_id>\d+)/other-names$",
        views.PersonOtherNamesView.as_view(),
        name="person-other-names",
    ),
    url(
        r"^person/(?P<person_id>\d+)/other-names/create$",
        views.PersonOtherNameCreateView.as_view(),
        name="person-other-name-create",
    ),
    url(
        r"^person/(?P<person_id>\d+)/other-name/(?P<pk>\d+)/delete$",
        views.PersonOtherNameDeleteView.as_view(),
        name="person-other-name-delete",
    ),
    url(
        r"^person/(?P<person_id>\d+)/other-name/(?P<pk>\d+)/update/?$",
        views.PersonOtherNameUpdateView.as_view(),
        name="person-other-name-update",
    ),
    url(
        r"^person/(?P<person_id>\d+)(?:/(?P<ignored_slug>.*))?$",
        views.PersonView.as_view(),
        name="person-view",
    ),
    url(
        r"^person/create/select_election$",
        views.NewPersonSelectElectionView.as_view(),
        name="person-create-select-election",
    ),
    url(
        r"^person/(?P<person_id>\d+)/update/?$",
        views.UpdatePersonView.as_view(),
        name="person-update",
    ),
    url(
        r"^person/(?P<person_id>\d+)/update/single_election_form/(?P<election>[^/]+)$",
        cache_page(60 * 60)(views.SingleElectionFormView.as_view()),
        name="person-update-single-election",
    ),
]

urlpatterns += [
    url(r"^numbers/", include("cached_counts.urls")),
    url(r"^moderation/", include("moderation_queue.urls")),
]
