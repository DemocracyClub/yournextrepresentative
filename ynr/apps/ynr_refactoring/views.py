from candidates.models import Ballot
from django.shortcuts import get_object_or_404
from django.urls import reverse
from django.views.generic import RedirectView
from elections.models import Election
from parties.models import Party

from .constants import UPDATED_SLUGS


# Redirect views
def get_changed_election_slug(slug):
    return UPDATED_SLUGS.get(slug, slug)


# Redirect views
class PermanentRedirectView(RedirectView):
    permanent = True

    def get(self, request, *args, **kwargs):
        if "election" in self.kwargs:
            self.kwargs["election"] = get_changed_election_slug(
                self.kwargs["election"]
            )
        return super().get(request, *args, **kwargs)


class RedirectConstituencyListView(PermanentRedirectView):
    """
    Moves from `/election/<election>/constituencies` URLs to
    /elections/<election>/ URLs

    """

    def get_redirect_url(self, *args, **kwargs):
        election = get_object_or_404(Election, slug=self.kwargs["election"])
        url = election.get_absolute_url()

        args = self.request.META.get("QUERY_STRING", "")
        if args and self.query_string:
            url = "%s?%s" % (url, args)
        return url


class RedirectPostsListView(PermanentRedirectView):
    """
    Moves the /posts URL to /elections/

    """

    url = "/elections/"


class RedirectConstituenciesUnlockedView(PermanentRedirectView):
    """
    Move /election/<election>/constituencies/unlocked to
    /elections/<election>/unlocked/

    """

    def get_redirect_url(self, *args, **kwargs):
        return reverse(
            "constituencies-unlocked",
            kwargs={"election": self.kwargs["election"]},
        )


class RedirectConstituencyDetailView(PermanentRedirectView):
    def get_redirect_url(self, *args, **kwargs):
        ballot = get_object_or_404(
            Ballot,
            election__slug=self.kwargs["election"],
            post__slug=self.kwargs["post_id"],
        )
        url = ballot.get_absolute_url()

        args = self.request.META.get("QUERY_STRING", "")
        if args and self.query_string:
            url = "%s?%s" % (url, args)
        return url


class RedirectConstituencyDetailCSVView(PermanentRedirectView):
    def get_redirect_url(self, *args, **kwargs):
        ballot = get_object_or_404(
            Ballot,
            election__slug=self.kwargs["election"],
            post__slug=self.kwargs["post_id"],
        )
        return "{}.csv".format(ballot.get_absolute_url().rstrip("/"))


class RedirectPartyDetailView(PermanentRedirectView):
    def get_redirect_url(self, *args, **kwargs):
        election = get_object_or_404(Election, slug=self.kwargs["election"])
        party = get_object_or_404(Party, legacy_slug=self.kwargs["legacy_slug"])

        return reverse(
            "candidates_by_election_for_party",
            kwargs={"election": election.slug, "party_id": party.ec_id},
        )
