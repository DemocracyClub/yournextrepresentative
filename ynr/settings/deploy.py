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
        "django-q": {
            "handlers": ["console"],
            "level": "INFO",
            "propagate": False,
        },
    },
}

# Certain errors are very noisy (obscuring the real problem) if this list is
# empty. FIXME: figure out a principled fix to this issue.
ADMINS = [("Dummy Admin", "dummy@example.com")]

CSRF_TRUSTED_ORIGINS = [
    f"https://{os.environ.get('FQDN')}",
]


# AWS X-Ray config
from aws_xray_sdk.core import patch_all, xray_recorder  # noqa

XRAY_SAMPLING_RULES = {
    "version": 2,
    "rules": [
        {
            "description": "YNR - Trace all requests at 100% for debugging",
            "host": "*",
            "http_method": "*",
            "url_path": "*",
            "fixed_target": 1,
            "rate": 1.0,
        }
    ],
    "default": {"fixed_target": 1, "rate": 1.0},
}

xray_recorder.configure(
    service="YNR-Django",
    sampling=True,  # Use sampling rules
    sampling_rules=XRAY_SAMPLING_RULES,
    context_missing="LOG_ERROR",
    daemon_address=os.environ.get("AWS_XRAY_DAEMON_ADDRESS", "127.0.0.1:2000"),
)

patch_all()
MIDDLEWARE.insert(0, "aws_xray_sdk.ext.django.middleware.XRayMiddleware")  # noqa
