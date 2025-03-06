import os

from .base_from_environment import *  # noqa

# TODO: constrain the values allowed in the env.
DEBUG = os.getenv("YNR_DEBUG", False)

# Log to stdout. Adapted from
# https://docs.djangoproject.com/en/4.2/topics/logging/#id4.
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
        },
    },
    "root": {
        "handlers": ["console"],
        "level": "WARNING",
    },
    "loggers": {
        "django": {
            "handlers": ["console"],
            "level": os.getenv("YNR_DJANGO_LOG_LEVEL", "INFO"),
            "propagate": False,
        },
    },
}

# FIXME: remove DummyCache.
CACHES = {"default": {"BACKEND": "django.core.cache.backends.dummy.DummyCache"}}

# Certain errors are very noisy (obscuring the real problem) if this list is
# empty. FIXME: figure out a principled fix to this issue.
ADMINS = [("Dummy Admin", "dummy@example.com")]
