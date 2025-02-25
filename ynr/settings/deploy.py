from .base_from_environment import *
import os

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
