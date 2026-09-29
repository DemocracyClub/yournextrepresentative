import re
import time

from django.contrib.auth import logout
from django.utils.cache import add_never_cache_headers


class DisableCachingForAuthenticatedUsers:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        return self.process_response(request, self.get_response(request))

    EXCLUDED_PATHS = (
        re.compile(r"^/static"),
        re.compile(r"^/media"),
        re.compile(r"^/ajax/ballots/ballots_for_select.json"),
    )

    def process_response(self, request, response):
        if (
            hasattr(request, "user")
            and request.user.is_authenticated
            and all(
                path_re.search(request.path) is None
                for path_re in self.EXCLUDED_PATHS
            )
        ):
            add_never_cache_headers(response)

        return response


class ApiAnonymousCacheMiddleware:
    """
    Adds a long-lived, stale-while-revalidate Cache-Control header to /api/
    responses that have neither an auth_token query param nor an
    Authorization header, and that don't already set their own
    Cache-Control (e.g. via a view's @cache_control decorator, or
    DisableCachingForAuthenticatedUsers for session-authenticated requests).
    """

    API_PATH_PREFIX = "/api/"
    # 1 hour, plus a day where a stale response can be served while revalidating
    ANON_CACHE_CONTROL = "max-age=3600, stale-while-revalidate=86400"

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        return self.process_response(request, self.get_response(request))

    def process_response(self, request, response):
        if (
            request.path.startswith(self.API_PATH_PREFIX)
            and "Cache-Control" not in response
            and "auth_token" not in request.GET
            and "HTTP_AUTHORIZATION" not in request.META
        ):
            response["Cache-Control"] = self.ANON_CACHE_CONTROL
        return response


class LogoutDisabledUsersMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        self.process_request(request)
        return self.get_response(request)

    def process_request(self, request):
        if (
            hasattr(request, "user")
            and request.user.is_authenticated
            and not request.user.is_active
        ):
            logout(request)


class RollingSessionExpiryMiddleware:
    """
    Push a signed-in user's session expiry back out to the full
    SESSION_COOKIE_AGE, at most once a day.

    Django only rewrites a session when something in it changes, so by default
    a session expires after SESSION_COOKIE_AGE, no matter how active the user has
    been. SESSION_SAVE_EVERY_REQUEST would give us a rolling expiry, but would
    add a Postgres UPDATE on every request.

    Writing a timestamp into the session gets us the same rolling expiry for
    one write per user per day. Assigning to the session marks it modified,
    which makes SessionMiddleware save it, and saving recalculates expire_date
    as now + SESSION_COOKIE_AGE and reissues the cookie with a fresh max-age.

    """

    # How much of the session's life to let elapse before extending it again.
    EXTEND_EVERY = 60 * 60 * 24
    # Where the time of the last extension is kept, in the session itself.
    SESSION_KEY = "_extended_at"

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        self.process_request(request)
        return self.get_response(request)

    def process_request(self, request):
        if not (hasattr(request, "user") and request.user.is_authenticated):
            return

        extended_at = request.session.get(self.SESSION_KEY)
        now = time.time()
        if extended_at is None or now - extended_at >= self.EXTEND_EVERY:
            request.session[self.SESSION_KEY] = now
