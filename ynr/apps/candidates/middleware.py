import re

from django.contrib.auth import logout
from django.utils.cache import add_never_cache_headers


class DisableCachingForAuthenticatedUsers:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.process_response(request, self.get_response(request))
        return response

    EXCLUDED_PATHS = (
        re.compile(r"^/static"),
        re.compile(r"^/media"),
        re.compile(r"^/ajax/ballots/ballots_for_select.json"),
    )

    def process_response(self, request, response):
        if hasattr(request, "user") and request.user.is_authenticated:
            if all(
                path_re.search(request.path) is None
                for path_re in self.EXCLUDED_PATHS
            ):
                add_never_cache_headers(response)

        return response


class LogoutDisabledUsersMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        self.process_request(request)
        response = self.get_response(request)
        return response

    def process_request(self, request):
        if (
            hasattr(request, "user")
            and request.user.is_authenticated
            and not request.user.is_active
        ):
            logout(request)
