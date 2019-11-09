import os

from .base import *  # noqa

DATABASES["default"]["CONN_MAX_AGE"] = 0  # noqa
SITE_NAME = "example.com"

CACHES = {"default": {"BACKEND": "django.core.cache.backends.dummy.DummyCache"}}


PASSWORD_HASHERS = ["django.contrib.auth.hashers.MD5PasswordHasher"]

RUNNING_TESTS = True

HAYSTACK_SIGNAL_PROCESSOR = "haystack.signals.RealtimeSignalProcessor"
HAYSTACK_CONNECTIONS = {
    "default": {
        "ENGINE": "haystack.backends.whoosh_backend.WhooshEngine",
        "STORAGE": "ram",
    }
}

SECRET_KEY = "just here for testing"
ALLOWED_HOSTS = ["candidates.democracyclub.org.uk"]

SHOW_SOPN_TRACKER = False
SHOW_RESULTS_PROGRESS = False

if os.environ.get("TRAVIS"):
    try:
        from .travis import *  # noqa
    except ImportError:
        pass
