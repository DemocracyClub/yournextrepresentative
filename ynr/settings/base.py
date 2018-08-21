"""
Default settings for YNR.

Settings in this file should only be changed if making an edit to the project,
not if just installing the project. For overriding settings per environment
set up a `local.py` file by following `local.example.py`.
"""

import os
from os.path import join, abspath, dirname
import sys


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

ALLOWED_HOSTS = []

SITE_ID = 1
SITE_NAME = "Democracy Club Candidates"

# Google analytics settings:
GOOGLE_ANALYTICS_ACCOUNT = "UA-52202336-3"
# This should be set to true unless you're using the old version of
# Google Analytics.
USE_UNIVERSAL_ANALYTICS = True

# The Twitter account referenced in the Twitter card data:
TWITTER_USERNAME = "democlub"

# The email address which is made public on the site for sending
# support email to:
SUPPORT_EMAIL = "candidates@democracyclub.org.uk"

# Email addresses that error emails are sent to when DEBUG = False
ADMINS = ()

# The From: address for all emails except error emails
DEFAULT_FROM_EMAIL = "candidates@democracyclub.org.uk"

# The From: address for error emails
SERVER_EMAIL = "candidates@democracyclub.org.uk"

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = None

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
                "ynr.context_processors.locale",
                "elections.uk.context_processors.site_wide_messages",
            ]
        },
    }
]

INSTALLED_APPS = (
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.humanize",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django.contrib.sites",
    "django_extensions",
    "pipeline",
    "sorl.thumbnail",
    "rest_framework",
    "rest_framework.authtoken",
    "images",
    "haystack",
    "elections",
    "popolo",
    "elections.uk",
    "candidates",
    "tasks",
    "cached_counts",
    "moderation_queue",
    "auth_helpers",
    "debug_toolbar",
    "template_timings_panel",
    "official_documents",
    "results",
    "notifications",
    "allauth",
    "allauth.account",
    "allauth.socialaccount",
    "allauth.socialaccount.providers.google",
    "allauth.socialaccount.providers.facebook",
    "allauth.socialaccount.providers.twitter",
    "corsheaders",
    "markdown_deux",
    "raven.contrib.django.raven_compat",
    "uk_results",
    "bulk_adding",
    "celery_haystack",
    "celery",
    "parties",
    "candidatebot",
    "resultsbot",
    "storages",
    "twitterbot",
)

MIDDLEWARE_CLASSES = (
    "debug_toolbar.middleware.DebugToolbarMiddleware",
    "corsheaders.middleware.CorsMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.locale.LocaleMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "candidates.middleware.LogoutDisabledUsersMiddleware",
    "candidates.middleware.CopyrightAssignmentMiddleware",
    "candidates.middleware.DisallowedUpdateMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "candidates.middleware.DisableCachingForAuthenticatedUsers",
)

# django-allauth settings:
AUTHENTICATION_BACKENDS = (
    # Needed to login by username in Django admin, regardless of `allauth`
    "django.contrib.auth.backends.ModelBackend",
    # `allauth` specific authentication methods, such as login by e-mail
    "allauth.account.auth_backends.AuthenticationBackend",
)


SOCIALACCOUNT_PROVIDERS = {
    "google": {
        "SCOPE": ["https://www.googleapis.com/auth/userinfo.profile"],
        "AUTH_PARAMS": {"access_type": "online"},
    },
    "facebook": {"SCOPE": ["email"]},
}

LOGIN_REDIRECT_URL = "/"
ACCOUNT_AUTHENTICATION_METHOD = "username_email"
ACCOUNT_EMAIL_VERIFICATION = "mandatory"
ACCOUNT_EMAIL_REQUIRED = True
ACCOUNT_FORMS = {
    "login": "ynr.forms.CustomLoginForm",
    "signup": "ynr.forms.CustomSignupForm",
}

ACCOUNT_USERNAME_REQUIRED = True
ACCOUNT_USERNAME_VALIDATORS = "ynr.helpers.allauth_validators"
SOCIALACCOUNT_AUTO_SIGNUP = True
ROOT_URLCONF = "ynr.urls"
WSGI_APPLICATION = "ynr.wsgi.application"

# Django Debug Toolbar settings:
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
    "debug_toolbar.panels.logging.LoggingPanel",
    "debug_toolbar.panels.redirects.RedirectsPanel",
]
INTERNAL_IPS = ["127.0.0.1"]

# Language settings (calculated above):
LOCALE_PATHS = [root("../locale")]
LANGUAGES = [("en", "English")]
LANGUAGE_CODE = "en-gb"
TIME_ZONE = "Europe/London"
USE_I18N = False
USE_L10N = False
USE_TZ = True
DD_MM_DATE_FORMAT_PREFERRED = True

# The media and static file settings:
MEDIA_ROOT = root("media")
MEDIA_URL = "/media/"

# Settings for staticfiles and Django pipeline:
STATIC_URL = "/static/"
STATIC_ROOT = root("static")

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
        },
        "official_documents": {
            "source_filenames": (
                "official_documents/css/official_documents.scss",
            ),
            "output_filename": "css/official_documents.css",
        },
        "bulk_adding": {
            "source_filenames": ("bulk_adding/css/bulk.scss",),
            "output_filename": "css/bulk_adding.css",
        },
        "all": {
            "source_filenames": (
                "candidates/style.scss",
                "cached_counts/style.scss",
                "select2/dist/css/select2.css",
                "jquery/jquery-ui.css",
                "jquery/jquery-ui.structure.css",
                "jquery/jquery-ui.theme.css",
                "moderation_queue/css/photo-upload.scss",
            ),
            "output_filename": "css/all.css",
        },
    },
    "JAVASCRIPT": {
        "image-review": {
            "source_filenames": (
                "moderation_queue/js/jquery.color.js",
                "moderation_queue/js/jquery.Jcrop.js",
                "moderation_queue/js/crop.js",
            ),
            "output_filename": "js/image-review.js",
        },
        "bulk_adding": {
            "source_filenames": ("bulk_adding/js/bulk.js",),
            "output_filename": "js/bulk_adding.js",
        },
        "all": {
            "source_filenames": (
                "jquery/jquery-1.11.1.js",
                "jquery/jquery-ui.js",
                "foundation/js/foundation/foundation.js",
                "foundation/js/foundation/foundation.equalizer.js",
                "foundation/js/foundation/foundation.dropdown.js",
                "foundation/js/foundation/foundation.tooltip.js",
                "foundation/js/foundation/foundation.offcanvas.js",
                "foundation/js/foundation/foundation.accordion.js",
                "foundation/js/foundation/foundation.joyride.js",
                "foundation/js/foundation/foundation.alert.js",
                "foundation/js/foundation/foundation.topbar.js",
                "foundation/js/foundation/foundation.reveal.js",
                "foundation/js/foundation/foundation.slider.js",
                "foundation/js/foundation/foundation.magellan.js",
                "foundation/js/foundation/foundation.clearing.js",
                "foundation/js/foundation/foundation.orbit.js",
                "foundation/js/foundation/foundation.interchange.js",
                "foundation/js/foundation/foundation.abide.js",
                "foundation/js/foundation/foundation.tab.js",
                "select2/dist/js/select2.full.js",
                "js/constituency.js",
                "js/person_form.js",
                "js/home_geolocation_form.js",
                "js/versions.js",
            ),
            "output_filename": "js/all.js",
        },
    },
    "COMPILERS": ("pipeline.compilers.sass.SASSCompiler",),
    "SASS_BINARY": "sassc",
    "CSS_COMPRESSOR": "pipeline.compressors.NoopCompressor",
    "JS_COMPRESSOR": "pipeline.compressors.yui.YUICompressor",
    # On some platforms this might be called "yuicompressor", so it may be
    # necessary to symlink it into your PATH as "yui-compressor".
    "YUI_BINARY": "/usr/bin/env yui-compressor",
}

SASS_INCLUDE_PATHS = (root("apps/candidates/static/foundation/scss"),)
SASS_ARGUMENT_LIST = ["-I " + p for p in SASS_INCLUDE_PATHS]
SASS_ARGUMENT_LIST.append("--style compressed")
SASS_ARGUMENT_LIST.append("--sourcemap")
PIPELINE["SASS_ARGUMENTS"] = " ".join(SASS_ARGUMENT_LIST)


SOURCE_HINTS = u"""
    Please don't quote third-party candidate sites \u2014 we prefer URLs of
    news stories or official candidate pages."""

# By default, cache successful results from MapIt for a day
EE_CACHE_SECONDS = 86400
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql_psycopg2",
        "NAME": "",
        # Note that there are various comments on the web
        # suggesting that settings CONN_MAX_AGE != 0 is a bad
        # idea when eventlet or gevent workers are being used.
        "CONN_MAX_AGE": 0 if DEBUG else 60,
    }
}

CACHES = {
    "default": {
        "TIMEOUT": None,  # cache keys never expire; we invalidate them
        "BACKEND": "django.core.cache.backends.memcached.MemcachedCache",
        "LOCATION": "127.0.0.1:11211",
        "KEY_PREFIX": DATABASES["default"]["NAME"],
    },
    "thumbnails": {
        "TIMEOUT": 60 * 60 * 24 * 2,  # expire after two days
        "BACKEND": "django.core.cache.backends.memcached.MemcachedCache",
        "LOCATION": "127.0.0.1:11211",
        "KEY_PREFIX": DATABASES["default"]["NAME"] + "-thumbnails",
    },
}

# sorl-thumbnail settings:
THUMBNAIL_CACHE = "thumbnails"
THUMBNAIL_DEBUG = DEBUG

# Settings for restricting user activity to reduce abuse:

# If this is true, you have to be in the 'Trusted to Rename' group in
# order to change the name of a candidate:
RESTRICT_RENAMES = False

# If this is set to false, then no edits of people are allowed.
EDITS_ALLOWED = True

SHOW_BANNER = False

# A bearer token for the Twitter API for mapping between
# Twitter usernames and IDs.
TWITTER_APP_ONLY_BEARER_TOKEN = None

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
}

# allow attaching extra data to notifications:
NOTIFICATIONS_USE_JSONFIELD = True

HAYSTACK_SIGNAL_PROCESSOR = "haystack.signals.RealtimeSignalProcessor"


HAYSTACK_CONNECTIONS = {
    "default": {
        "ENGINE": "haystack.backends.whoosh_backend.WhooshEngine",
        "PATH": ".haystack",
    }
}

# CORS config
CORS_ORIGIN_ALLOW_ALL = True
CORS_URLS_REGEX = r"^/(api|upcoming-elections)/.*$"
CORS_ALLOW_METHODS = ("GET", "OPTIONS")

MARKDOWN_DEUX_STYLES = {
    "default": {
        "extras": {"code-friendly": None, "fenced-code-blocks": None},
        "safe_mode": "escape",
    }
}

# TODO Delete this once election specific import are gone
ELECTION_APP = "uk"
ELECTION_APP_FULLY_QUALIFIED = "elections.uk"

CANDIDATES_REQUIRED_FOR_WEIGHTED_PARTY_LIST = 20
HOIST_ELECTED_CANDIDATES = True


RESULTS_FEATURE_ACTIVE = True
CAN_EDIT_ELECTIONS = False
DATE_FORMAT = "jS E Y"

SITE_OWNER = "Democracy Club"
COPYRIGHT_HOLDER = "Democracy Club Community Interest Company"

IMAGE_PROXY_URL = ""

RESULTS_FEATURE_ACTIVE = False


LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "filters": {
        "require_debug_false": {"()": "django.utils.log.RequireDebugFalse"}
    },
    "handlers": {
        "mail_admins": {
            "level": "ERROR",
            "filters": ["require_debug_false"],
            "class": "django.utils.log.AdminEmailHandler",
        }
    },
    "loggers": {
        "elasticsearch": {
            "handlers": ["mail_admins"],
            "level": "ERROR",
            "propagate": True,
        }
    },
}


CANDIDATE_BOT_USERNAME = "CandidateBot"
RESULTS_BOT_USERNAME = "ResultsBot"
TWITTER_BOT_USERNAME = "TwitterBot"

# import application constants
from .constants.needs_review import *  # noqa

from ynr_refactoring.settings import *  # noqa

# .local.py overrides all the common settings.
try:
    from .local import *  # noqa
except ImportError:
    from django.utils.termcolors import colorize

    print(
        colorize(
            "WARNING: no local settings file found. See local.py.example",
            fg="red",
        )
    )


def _is_running_tests():
    if len(sys.argv) > 1 and sys.argv[1] in ["test"]:
        return True
    if os.environ.get("RUN_ENV") == "test":
        return True
    return False


if _is_running_tests():
    from .testing import *  # noqa
