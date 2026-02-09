# dev.py
# Set things here that we want to always be true in dev
# but don't make sense in any deployed environment

import contextlib
import socket

from .base import *  # noqa: F403

# Only set DEBUG to True in development environments
DEBUG = True

DC_ENVIRONMENT = "local"

EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"

SOPN_UPDATE_NOTIFICATION_EMAILS = ["developers@democracyclub.org.uk"]

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
INSTALLED_APPS += ["debug_toolbar", "template_timings_panel"]  # noqa: F405
MIDDLEWARE += ["debug_toolbar.middleware.DebugToolbarMiddleware"]  # noqa: F405

# Add the container's internal IPs to the list of those IPs permitted
# to access the Django debug toolbar, which allows it to be enabled.
INTERNAL_IPS = [
    "127.0.0.1",
    socket.gethostbyname(socket.gethostname()),
]
with contextlib.suppress(socket.gaierror):
    INTERNAL_IPS.append(socket.gethostbyname("host.docker.internal"))


with contextlib.suppress(ImportError):
    from .local import *  # noqa: F403

USE_DUMMY_PDF_EXTRACTOR = True
