# dev.py
# Set things here that we want to always be true in dev
# but don't make sense in any deployed environment

import contextlib
import socket

from .base import *  # noqa: F403

# Only set DEBUG to True in development environments
DEBUG = True

EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"

SECRET_KEY = "django-insecure-fake"

# TODO: should we actually just use DB cache in dev too?
CACHES = {"default": {"BACKEND": "django.core.cache.backends.dummy.DummyCache"}}

# Some errors are very noisy (obscuring the real problem) if this list is empty
ADMINS = [("Dummy Admin", "dummy@example.com")]


# Django debug toolbar
DEBUG_TOOLBAR_PATCH_SETTINGS = (False,)
DEBUG_TOOLBAR_PANELS = [
    "debug_toolbar.panels.versions.VersionsPanel",
    "debug_toolbar.panels.timer.TimerPanel",
    "debug_toolbar.panels.settings.SettingsPanel",
    "debug_toolbar.panels.headers.HeadersPanel",
    "debug_toolbar.panels.request.RequestPanel",
    "debug_toolbar.panels.sql.SQLPanel",
    "debug_toolbar.panels.staticfiles.StaticFilesPanel",
    "debug_toolbar.panels.templates.TemplatesPanel",
    "debug_toolbar.panels.cache.CachePanel",
    "debug_toolbar.panels.signals.SignalsPanel",
    "debug_toolbar.panels.redirects.RedirectsPanel",
]
INSTALLED_APPS += ["debug_toolbar"]  # noqa: F405
MIDDLEWARE += ["debug_toolbar.middleware.DebugToolbarMiddleware"]  # noqa: F405

# This unpleasantness adds the container's internal IP to the list of those IPs
# permitted to access the Django debug toolbar, which allows it to be enabled.
# We believe the container's own IP needs to be in this list because of
# something to do with the container networking, or the HTTP server gunicorn's
# reverse-proxy setup, or both.
# TODO: Replace with a better method, either here or by changing the
# container/gunicorn setup. https://pypi.org/project/netifaces/ also exists,
# but might not be considered "better".
s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
s.connect(("8.8.8.8", 80))
INTERNAL_IPS = ["127.0.0.1", str(s.getsockname()[0])]
s.close()


with contextlib.suppress(ImportError):
    from .local import *  # noqa: F403
