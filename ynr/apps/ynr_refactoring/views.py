from django.views.generic import RedirectView
from django.views.defaults import page_not_found
from django.core.urlresolvers import reverse
from django.shortcuts import get_object_or_404

from elections.models import Election

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
