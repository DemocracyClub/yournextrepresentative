from django.views.generic import RedirectView
from django.views.defaults import page_not_found
from django.core.urlresolvers import reverse
from django.shortcuts import get_object_or_404

from elections.models import Election
from candidates.models import PostExtraElection
from parties.models import Party

from .models import PageNotFoundLog


def logged_page_not_found_wrapper(request, *args, **kwargs):
    # Log stuff
    PageNotFoundLog(url=request.path).save()
    return page_not_found(request, *args, **kwargs)


# Redirect views


class PermanentRedirectView(RedirectView):
    permanent = True


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
            PostExtraElection,
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
            PostExtraElection,
            election__slug=self.kwargs["election"],
            post__slug=self.kwargs["post_id"],
        )
        url = "{}.csv".format(ballot.get_absolute_url().rstrip("/"))

        return url


class RedirectPartyDetailView(PermanentRedirectView):
    def get_redirect_url(self, *args, **kwargs):
        election = get_object_or_404(Election, slug=self.kwargs["election"])
        party = get_object_or_404(Party, legacy_slug=self.kwargs["legacy_slug"])

        return reverse(
            "candidates_by_election_for_party",
            kwargs={"election": election.slug, "party_id": party.ec_id},
        )
