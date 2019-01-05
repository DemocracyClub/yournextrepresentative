from django.conf import settings
from django.conf.urls import include, url
from django.contrib import admin
from django.views.generic import TemplateView
from django.views.generic.base import RedirectView
from django.views.decorators.cache import cache_page

import candidates.views as views
import elections.views
import parties.views

from .feeds import RecentChangesFeed, NeedsReviewFeed
from .constants import ELECTION_ID_REGEX, POST_ID_REGEX


urlpatterns = [
    url(
        r"^api-auth/",
        include("rest_framework.urls", namespace="rest_framework"),
    ),
    url(r"^", include(settings.ELECTION_APP_FULLY_QUALIFIED + ".urls")),
]

patterns_to_format = [
    {
        "pattern": r"^election/{election}/post/{post}/record-winner$",
        "view": views.ConstituencyRecordWinnerView.as_view(),
        "name": "record-winner",
    },
    {
        "pattern": r"^election/{election}/post/{post}/retract-winner$",
        "view": views.ConstituencyRetractWinnerView.as_view(),
        "name": "retract-winner",
    },
    {
        "pattern": r"^election/{election}/post/{post}/(?P<ignored_slug>.*).csv$",
        "view": views.ConstituencyDetailCSVView.as_view(),
        "name": "constituency_csv",
    },
    {
        "pattern": r"^election/{election}/post/lock$",
        "view": views.ConstituencyLockView.as_view(),
        "name": "constituency-lock",
    },
    {
        "pattern": r"^election/{election}/candidacy$",
        "view": views.CandidacyView.as_view(),
        "name": "candidacy-create",
    },
    {
        "pattern": r"^election/{election}/candidacy/delete$",
        "view": views.CandidacyDeleteView.as_view(),
        "name": "candidacy-delete",
    },
    {
        "pattern": r"^election/{election}/person/create/$",
        "view": views.NewPersonView.as_view(),
        "name": "person-create",
    },
    {
        "pattern": r"^person/create/select_election$",
        "view": views.NewPersonSelectElectionView.as_view(),
        "name": "person-create-select-election",
    },
    {
        "pattern": r"^person/(?P<person_id>\d+)/update/?$",
        "view": views.UpdatePersonView.as_view(),
        "name": "person-update",
    },
    {
        "pattern": r"^person/(?P<person_id>\d+)/update/single_election_form/{election}$",
        "view": cache_page(60 * 60)(views.SingleElectionFormView.as_view()),
        "name": "person-update-single-election",
    },
    {
        "pattern": r"^update-disallowed$",
        "view": TemplateView.as_view(
            template_name="candidates/update-disallowed.html"
        ),
        "name": "update-disallowed",
    },
    {
        "pattern": r"^all-edits-disallowed$",
        "view": TemplateView.as_view(
            template_name="candidates/all-edits-disallowed.html"
        ),
        "name": "all-edits-disallowed",
    },
    {
        "pattern": r"^person/(?P<person_id>\d+)/revert$",
        "view": views.RevertPersonView.as_view(),
        "name": "person-revert",
    },
    {
        "pattern": r"^person/(?P<person_id>\d+)/merge$",
        "view": views.MergePeopleView.as_view(),
        "name": "person-merge",
    },
    {
        "pattern": r"^person/(?P<person_id>\d+)/other-names$",
        "view": views.PersonOtherNamesView.as_view(),
        "name": "person-other-names",
    },
    {
        "pattern": r"^person/(?P<person_id>\d+)/other-names/create$",
        "view": views.PersonOtherNameCreateView.as_view(),
        "name": "person-other-name-create",
    },
    {
        "pattern": r"^person/(?P<person_id>\d+)/other-name/(?P<pk>\d+)/delete$",
        "view": views.PersonOtherNameDeleteView.as_view(),
        "name": "person-other-name-delete",
    },
    {
        "pattern": r"^person/(?P<person_id>\d+)/other-name/(?P<pk>\d+)/update/?$",
        "view": views.PersonOtherNameUpdateView.as_view(),
        "name": "person-other-name-update",
    },
    {
        "pattern": r"^person/(?P<person_id>\d+)(?:/(?P<ignored_slug>.*))?$",
        "view": views.PersonView.as_view(),
        "name": "person-view",
    },
    {
        "pattern": r"^areas/(?P<type_and_area_ids>.*?)(?:/(?P<ignored_slug>.*))?$",
        "view": views.AreasView.as_view(),
        "name": "areas-view",
    },
    {
        "pattern": r"^posts-of-type/(?P<post_type>.*?)(?:/(?P<ignored_slug>.*))?$",
        "view": views.PostsOfTypeView.as_view(),
        "name": "posts-of-type-view",
    },
    {
        "pattern": r"^election/{election}/party/(?P<legacy_slug>[^/]+)/(?P<ignored_slug>.*)$",
        "view": parties.views.PartyDetailView.as_view(),
        "name": "party",
    },
    {
        "pattern": r"^election/{election}/parties/?$",
        "view": parties.views.PartyListView.as_view(),
        "name": "party-list",
    },
    {
        "pattern": r"^recent-changes$",
        "view": views.RecentChangesView.as_view(),
        "name": "recent-changes",
    },
    {
        "pattern": r"^leaderboard$",
        "view": views.LeaderboardView.as_view(),
        "name": "leaderboard",
    },
    {
        "pattern": r"^leaderboard/contributions.csv$",
        "view": views.UserContributions.as_view(),
        "name": "user-contributions",
    },
    {
        "pattern": r"^feeds/changes.xml$",
        "view": RecentChangesFeed(),
        "name": "changes_feed",
    },
    {
        "pattern": r"^feeds/needs-review.xml$",
        "view": NeedsReviewFeed(),
        "name": "needs-review_feed",
    },
    {
        "pattern": r"^help/api$",
        "view": views.HelpApiView.as_view(),
        "name": "help-api",
    },
    {
        "pattern": r"^help/results$",
        "view": views.HelpResultsView.as_view(),
        "name": "help-results",
    },
    {
        "pattern": r"^help/about$",
        "view": views.HelpAboutView.as_view(),
        "name": "help-about",
    },
    {
        "pattern": r"^help/privacy$",
        "view": RedirectView.as_view(
            url="https://democracyclub.org.uk/privacy/", permanent=True
        ),
        "name": "help-privacy",
    },
    {
        "pattern": r"^help/photo-policy$",
        "view": TemplateView.as_view(
            template_name="candidates/photo-policy.html"
        ),
        "name": "help-photo-policy",
    },
    {
        "pattern": r"^copyright-question$",
        "view": views.AskForCopyrightAssigment.as_view(),
        "name": "ask-for-copyright-assignment",
    },
    {
        "pattern": r"^search$",
        "view": views.PersonSearch.as_view(),
        "name": "person-search",
    },
]

urlpatterns += [
    url(
        p["pattern"].format(election=ELECTION_ID_REGEX, post=POST_ID_REGEX),
        p["view"],
        name=p["name"],
    )
    for p in patterns_to_format
]

urlpatterns += [
    url(r"^numbers/", include("cached_counts.urls")),
    url(r"^moderation/", include("moderation_queue.urls")),
]
