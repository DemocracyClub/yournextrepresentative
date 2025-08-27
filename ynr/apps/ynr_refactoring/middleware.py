"""

Copied from https://github.com/DemocracyClub/dc_django_utils/blob/main/dc_utils/middleware.py

We can't install that library due to version compatibility with Django Pipeline.

When we upgrade pipeline, we can use dc_utils and remove this code.

Until then, this gets us someting useful up and running.

"""

import fnmatch
import os

from django.conf import settings
from django.http import HttpResponse


class BasicAuthMiddleware:
    def __init__(self, get_response):
        dc_environment = os.environ.get("DC_ENVIRONMENT", "")
        self.auth_enabled = getattr(
            settings,
            "BASIC_AUTH_ENABLED",
            dc_environment in ("staging", "development"),
        )

        self.get_response = get_response
        self.required_auth_header = getattr(
            settings, "BASIC_AUTH_VALUE", "Basic ZGM6ZGM="
        )  # "dc:dc" in base64

    def __call__(self, request):
        if not self.auth_enabled:
            return self.get_response(request)

        # Check for Authorization header
        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header == self.required_auth_header:
            return self.get_response(request)

        for pattern in getattr(settings, "BASIC_AUTH_ALLOWLIST", []):
            if fnmatch.fnmatch(request.path.rstrip("/"), pattern.rstrip("/")):
                return self.get_response(request)

        # If authorization fails, return 401 Unauthorized
        response = HttpResponse("Unauthorized", status=401)
        response["WWW-Authenticate"] = 'Basic realm="Restricted"'
        return response
