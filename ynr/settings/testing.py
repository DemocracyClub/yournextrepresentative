import os
from tempfile import mkdtemp

from .base import *  # noqa

DATABASES["default"]["CONN_MAX_AGE"] = 0  # noqa
SITE_NAME = "example.com"
if os.environ.get("CIRCLECI"):
    DATABASES["default"]["NAME"] = "ynr"  # noqa
    DATABASES["default"]["USER"] = "ynr"  # noqa


class DisableMigrations(object):
    def __contains__(self, item):
        return True

    def __getitem__(self, item):
        return None


MIGRATION_MODULES = DisableMigrations()

CACHES = {"default": {"BACKEND": "django.core.cache.backends.dummy.DummyCache"}}

REST_FRAMEWORK["DEFAULT_THROTTLE_RATES"] = {"anon": "1000/minute"}  # noqa

PASSWORD_HASHERS = ["django.contrib.auth.hashers.MD5PasswordHasher"]

RUNNING_TESTS = True

SECRET_KEY = "just here for testing"
ALLOWED_HOSTS = ["candidates.democracyclub.org.uk"]

SHOW_SOPN_TRACKER = False
SHOW_RESULTS_PROGRESS = False

ALWAYS_ALLOW_RESULT_RECORDING = False

DEFAULT_FILE_STORAGE = "ynr.storages.TestMediaStorage"
MEDIA_ROOT = mkdtemp()

FRONT_PAGE_CTA = "BY_ELECTIONS"
