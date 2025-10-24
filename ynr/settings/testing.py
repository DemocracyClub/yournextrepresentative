# testing.py
# Set things here that we want to always be true when running unit tests

from tempfile import mkdtemp

from .base import *  # noqa: F403

RUNNING_TESTS = True

DC_ENVIRONMENT = "testing"


class DisableMigrations(object):
    def __contains__(self, item):
        return True

    def __getitem__(self, item):
        return None


SITE_NAME = "example.com"

MIGRATION_MODULES = DisableMigrations()

CACHES = {"default": {"BACKEND": "django.core.cache.backends.dummy.DummyCache"}}

REST_FRAMEWORK["DEFAULT_THROTTLE_RATES"] = {"anon": "1000/minute"}  # noqa: F405

PASSWORD_HASHERS = ["django.contrib.auth.hashers.MD5PasswordHasher"]

SECRET_KEY = "django-insecure-fake"
ALLOWED_HOSTS = ["candidates.democracyclub.org.uk"]

SHOW_SOPN_TRACKER = False
SHOW_RESULTS_PROGRESS = False

ALWAYS_ALLOW_RESULT_RECORDING = False

DEFAULT_FILE_STORAGE = "ynr.storages.TestMediaStorage"
MEDIA_ROOT = mkdtemp()

FRONT_PAGE_CTA = "BY_ELECTIONS"

SOPN_UPDATE_NOTIFICATION_EMAILS = ["developers@democracyclub.org.uk"]


# override these settings to safe values if they are set from the env
TWITTER_APP_ONLY_BEARER_TOKEN = None
OPEN_AI_API_KEY = None
MASTODON_APP_ONLY_BEARER_TOKEN = None
HCAPTCHA_SITEKEY = None
HCAPTCHA_SECRET = None
S3_MEDIA_BUCKET = None
S3_MEDIA_REGION = None
TEXTRACT_S3_BUCKET_NAME = None
TEXTRACT_S3_BUCKET_REGION = None
TEXTRACT_S3_BUCKET_URL = None
EMAIL_HOST = None
EMAIL_HOST_USER = None
EMAIL_HOST_PASSWORD = None
SLACK_TOKEN = None
DEFAULT_FROM_EMAIL = "candidates@example.com"
ENABLE_SCHEDULED_JOBS = False
