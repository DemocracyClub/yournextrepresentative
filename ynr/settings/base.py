import os
import sys
from os.path import abspath, dirname, join
from pathlib import Path


def str_bool_to_bool(str_bool):
    if not str_bool:
        return False
    return str_bool in ["1", "True", "true", "TRUE"]


# PATH vars
def here(*path):
    return join(abspath(dirname(__file__)), *path)


def root(*path):
    return abspath(join(abspath(here("..")), *path))


sys.path.insert(0, root("apps"))
PROJECT_ROOT = here("..")
ROOT = PROJECT_ROOT
BASE_DIR = root("..")

DEBUG = False

INTERNAL_IPS = [
    "127.0.0.1",
    "localhost",
]

# In an AWS-ECS-behind-ALB context, the ALB's health checks don't yet arrive
# with a meaningful HTTP host header. We currently rely on the ALB to route
# only appropriate requests to the webapp, and can therefore nullify Django's
# protections as they no longer apply in any deployed environment.
# This also does not matter in local dev
ALLOWED_HOSTS = ["*"]

SITE_ID = 1
SITE_NAME = "Democracy Club Candidates"

# The Twitter account referenced in the Twitter card data:
TWITTER_USERNAME = "democlub"

# The email address which is made public on the site for sending
# support email to:
SUPPORT_EMAIL = "candidates@democracyclub.org.uk"


# The From: address for all emails except error emails
DEFAULT_FROM_EMAIL = "candidates@democracyclub.org.uk"

SECRET_KEY = os.environ.get("DJANGO_SECRET_KEY", None)

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [root("templates"), root("ynr", "templates")],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "django.template.context_processors.media",
                "django.template.context_processors.request",
                "django.template.context_processors.debug",
                "django.template.context_processors.static",
                "django.template.context_processors.tz",
                "ynr.context_processors.add_group_permissions",
                "ynr.context_processors.add_notification_data",
                "ynr.context_processors.add_settings",
                "ynr.context_processors.add_site",
                "ynr.context_processors.election_date",
                "frontend.context_processors.site_wide_banner",
                "wombles.context_processors.action_counts_processor",
            ]
        },
    }
]

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.humanize",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django.contrib.sites",
    "django.contrib.postgres",
    "django_extensions",
    "django_q",
    "django_q_registry",
    "pipeline",
    "sorl.thumbnail",
    "rest_framework",
    "rest_framework.authtoken",
    "django_filters",
    "elections",
    "popolo",
    "elections.uk",
    "candidates",
    "cached_counts",
    "moderation_queue",
    "auth_helpers",
    "template_timings_panel",
    "official_documents",
    "results",
    "corsheaders",
    "uk_results",
    "bulk_adding",
    "parties",
    "candidatebot",
    "resultsbot",
    "storages",
    "twitterbot",
    "api",
    "people",
    "ynr_refactoring",
    "wombles",
    "frontend",
    "sopn_parsing",
    "facebook_data",
    "search",
    "duplicates",
    "data_exports",
    "django_svelte",
    "hcaptcha",
]

DEFAULT_AUTO_FIELD = "django.db.models.AutoField"

MIDDLEWARE = [
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "corsheaders.middleware.CorsMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "candidates.middleware.LogoutDisabledUsersMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "candidates.middleware.DisableCachingForAuthenticatedUsers",
    "wombles.middleware.CheckProfileDetailsMiddleware",
    "ynr_refactoring.middleware.BasicAuthMiddleware",
]

AUTHENTICATION_BACKENDS = (
    "sesame.backends.ModelBackend",
    "django.contrib.auth.backends.ModelBackend",
)

SESAME_MAX_AGE = 60 * 60  # 1 hour
SESAME_ONE_TIME = False
SESAME_TOKEN_NAME = "login_token"

BASIC_AUTH_ALLOWLIST = [
    "/status_check/",  # load balancer health check
    "/api/next/*",  # Allow next API
]

LOGIN_REDIRECT_URL = "/"

ROOT_URLCONF = "ynr.urls"
WSGI_APPLICATION = "ynr.wsgi.application"

# Language settings (calculated above):
LANGUAGES = [("en-gb", "British English")]
LANGUAGE_CODE = "en-gb"
TIME_ZONE = "Europe/London"
USE_I18N = False
USE_TZ = True
DD_MM_DATE_FORMAT_PREFERRED = True

# The media and static file settings:
MEDIA_ROOT = root("media")
MEDIA_URL = "/media/"

# Settings for staticfiles and Django pipeline:
SOPN__MATCHER_PATH = (
    Path(str(PROJECT_ROOT)) / "apps/official_documents/SOPNMatcherInterface"
)
STATIC_URL = "/static/"
STATIC_ROOT = root("static")
STATICFILES_DIRS = (
    os.path.abspath(os.path.join(BASE_DIR, "vendor_assets")),
    SOPN__MATCHER_PATH / "dist" / "assets",
)

STATICFILES_LOCATION = "static"
MEDIAFILES_LOCATION = "media"
STATICFILES_STORAGE = "ynr.storages.StaticStorage"
STATICFILES_FINDERS = (
    "django.contrib.staticfiles.finders.FileSystemFinder",
    "django.contrib.staticfiles.finders.AppDirectoriesFinder",
    "pipeline.finders.CachedFileFinder",
    "pipeline.finders.PipelineFinder",
    "pipeline.finders.ManifestFinder",
)

PIPELINE = {
    "STYLESHEETS": {
        "image-review": {
            "source_filenames": (
                "moderation_queue/css/jquery.Jcrop.css",
                "moderation_queue/css/crop.scss",
            ),
            "output_filename": "css/image-review.css",
            "extra_context": {"media": "screen"},
        },
        "official_documents": {
            "source_filenames": (
                "official_documents/css/official_documents.scss",
            ),
            "output_filename": "css/official_documents.css",
            "extra_context": {"media": "screen"},
        },
        "bulk_adding": {
            "source_filenames": ("bulk_adding/css/bulk.scss",),
            "output_filename": "css/bulk_adding.css",
            "extra_context": {"media": "screen"},
        },
        "all": {
            "source_filenames": (
                "candidates/style.scss",
                "cached_counts/style.scss",
                "scss/select2.css",
                "moderation_queue/css/photo-upload.scss",
                "frontend/css/frontend.scss",
            ),
            "output_filename": "css/all.css",
            "extra_context": {"media": "screen"},
        },
    },
    "JAVASCRIPT": {
        "image-review": {
            "source_filenames": (
                "moderation_queue/js/jquery.color.js",
                "moderation_queue/js/jquery.Jcrop.js",
                "moderation_queue/js/crop.js",
                "js/sorttable.js",
            ),
            "output_filename": "js/image-review.js",
        },
        "bulk_adding": {
            "source_filenames": ("bulk_adding/js/bulk.js",),
            "output_filename": "js/bulk_adding.js",
        },
        "sopn_viewer": {
            "source_filenames": ("official_documents/js/sopn_viewer.js",),
            "output_filename": "js/sopn_viewer.js",
        },
        "all": {
            "source_filenames": (
                "js/jquery.js",
                "js/foundation.js",
                "js/select2.full.js",
                "js/ballot.js",
                "js/person_form.js",
                "js/home_geolocation_form.js",
                "js/versions.js",
                "js/results.js",
            ),
            "output_filename": "js/all.js",
        },
    },
    "COMPILERS": ("pipeline.compilers.sass.SASSCompiler",),
    "SASS_BINARY": "pysassc",
    "CSS_COMPRESSOR": "pipeline.compressors.NoopCompressor",
    "JS_COMPRESSOR": "pipeline.compressors.NoopCompressor",
    # On some platforms this might be called "yuicompressor", so it may be
    # necessary to symlink it into your PATH as "yui-compressor".
    "YUI_BINARY": "/usr/bin/env yui-compressor",
    # Don't munge function names, meaning they can be used globally
    "YUI_JS_ARGUMENTS": "--nomunge",
}

SASS_INCLUDE_PATHS = (
    os.path.abspath(os.path.join(BASE_DIR, "vendor_assets/scss")),
)
SASS_ARGUMENT_LIST = ["-I " + p for p in SASS_INCLUDE_PATHS]
SASS_ARGUMENT_LIST.append("--style compressed")
PIPELINE["SASS_ARGUMENTS"] = " ".join(SASS_ARGUMENT_LIST)

SOURCE_HINTS = """
    Please don't quote third-party candidate sites \u2014 we prefer URLs of
    news stories or official candidate pages."""

# By default, cache successful results from Every Election for a day
EE_CACHE_SECONDS = 86400

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": os.environ.get("POSTGRES_DBNAME", ""),
        "USER": os.environ.get("POSTGRES_USERNAME", ""),
        "PASSWORD": os.environ.get("POSTGRES_PASSWORD", ""),
        "HOST": os.environ.get("POSTGRES_HOST", ""),
        "CONN_MAX_AGE": 0,
    }
}


def get_qcluster_settings(minimum_cron_interval_seconds):
    # kill jobs if they haven't completed in $TIMEOUT seconds
    TIMEOUT = 240
    # retry must be a number greater than timeout
    # and less than minimum_cron_interval_seconds.
    # We can't't have scheduled tasks that run
    # more frequently than every $RETRY seconds
    RETRY = TIMEOUT + (minimum_cron_interval_seconds - TIMEOUT) / 2

    assert TIMEOUT < RETRY < minimum_cron_interval_seconds

    return {
        "name": "DjangORM",
        "workers": 2,
        "queue_limit": 50,
        "bulk": 10,
        "orm": "default",
        # schedule-friendly settings
        # TODO: review once we have proper background tasks
        "catch_up": False,
        "timeout": TIMEOUT,
        "max_attempts": 1,  # no retries
        "retry": RETRY,
    }


# MINIMUM_CRON_INTERVAL is the most frequently we're allowed to
# run a scheduled job. So if we set this to 5
# then */5 is the most often we're allowed to run a scheduled job
MINIMUM_CRON_INTERVAL_MINUTES = 5
Q_CLUSTER = get_qcluster_settings(MINIMUM_CRON_INTERVAL_MINUTES * 60)

CACHES = {
    "default": {
        "TIMEOUT": None,  # cache keys never expire; we invalidate them
        "BACKEND": "django.core.cache.backends.db.DatabaseCache",
        "LOCATION": "ynr_cache",
    }
}

# sorl-thumbnail settings:
THUMBNAIL_CACHE = "thumbnails"
THUMBNAIL_DEBUG = DEBUG

# Settings for restricting user activity to reduce abuse:

# If this is set to false, then no edits of people are allowed.
EDITS_ALLOWED = True

# If set to False, new users won't be allowed to make accounts
# Useful for pre-election anti-vandalism
NEW_USER_ACCOUNT_CREATION_ALLOWED = True

# A bearer token for the Twitter API for mapping between
# Twitter usernames and IDs.
TWITTER_APP_ONLY_BEARER_TOKEN = os.environ.get(
    "TWITTER_APP_ONLY_BEARER_TOKEN", None
)

OPEN_AI_API_KEY = os.environ.get("OPEN_AI_API_KEY", None)

# A bearer token for the Mastodon API for mapping between
# Mastodon usernames and IDs.
MASTODON_APP_ONLY_BEARER_TOKEN = os.environ.get(
    "MASTODON_APP_ONLY_BEARER_TOKEN", None
)


# Django Rest Framework settings:
REST_FRAMEWORK = {
    "DEFAULT_PERMISSION_CLASSES": ("candidates.api_permissions.ReadOnly",),
    "DEFAULT_VERSIONING_CLASS": "rest_framework.versioning.URLPathVersioning",
    "DEFAULT_FILTER_BACKENDS": (
        "django_filters.rest_framework.DjangoFilterBackend",
    ),
    "DEFAULT_RENDERER_CLASSES": (
        "rest_framework.renderers.JSONRenderer",
        "rest_framework_jsonp.renderers.JSONPRenderer",
        "rest_framework.renderers.BrowsableAPIRenderer",
    ),
    "PAGE_SIZE": 10,
    "DEFAULT_PAGINATION_CLASS": "rest_framework.pagination.PageNumberPagination",
    "DEFAULT_SCHEMA_CLASS": "rest_framework.schemas.coreapi.AutoSchema",
    "DEFAULT_AUTHENTICATION_CLASSES": (
        "api.next.authentication.TokenAuthSupportQueryString",
    ),
    "DEFAULT_THROTTLE_CLASSES": ("rest_framework.throttling.AnonRateThrottle",),
    "DEFAULT_THROTTLE_RATES": {"anon": "10/minute"},
}

# CORS config
CORS_ORIGIN_ALLOW_ALL = True
CORS_URLS_REGEX = r"^/(api|upcoming-elections)/.*$"
CORS_ALLOW_METHODS = ("GET", "OPTIONS")

# TODO Delete this once election specific import are gone
ELECTION_APP = "uk"
ELECTION_APP_FULLY_QUALIFIED = "elections.uk"

HOIST_ELECTED_CANDIDATES = True

RESULTS_FEATURE_ACTIVE = True
CAN_EDIT_ELECTIONS = False
FORMAT_MODULE_PATH = "ynr.settings.constants.formats"

SITE_OWNER = "Democracy Club"
COPYRIGHT_HOLDER = "Democracy Club Community Interest Company"

IMAGE_PROXY_URL = ""

RESULTS_FEATURE_ACTIVE = False


CANDIDATE_BOT_USERNAME = "CandidateBot"
RESULTS_BOT_USERNAME = "ResultsBot"
TWITTER_BOT_USERNAME = "TwitterBot"

SOPN_UPDATE_NOTIFICATION_EMAILS = os.environ.get(
    "SOPN_UPDATE_NOTIFICATION_EMAILS", "developers@democracyclub.org.uk"
).split(",")

# The maximum number of fields that can be uploaded in a single request.
DATA_UPLOAD_MAX_NUMBER_FIELDS = 3000


HCAPTCHA_SITEKEY = os.environ.get("HCAPTCHA_SITEKEY", None)
HCAPTCHA_SECRET = os.environ.get("HCAPTCHA_SECRET", None)

ENABLE_SCHEDULED_JOBS = str_bool_to_bool(
    os.environ.get("ENABLE_SCHEDULED_JOBS", False)
)

# import application constants
from .constants.needs_review import *  # noqa
from .constants.csv_fields import *  # noqa
from .constants.nuts import *  # noqa
from .constants.sopn_parsing import *  # noqa
from .constants.home_page_cta import *  # noqa

from ynr_refactoring.settings import *  # noqa


RUNNING_TESTS = False
