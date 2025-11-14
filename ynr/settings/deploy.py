# deploy.py
# Set things here that we want to be true in ALL deployed environments
# but don't make sense in local dev

import os

import sentry_sdk
from sentry_sdk.integrations import django

from .base import *  # noqa: F403

DEBUG = False

DC_ENVIRONMENT = os.environ["DC_ENVIRONMENT"]

SECRET_KEY = os.environ["DJANGO_SECRET_KEY"]

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
        "aws_xray_sdk": {
            "handlers": ["console"],
            "level": "CRITICAL",
            "propagate": False,
        },
    },
}

# Certain errors are very noisy (obscuring the real problem) if this list is
# empty. FIXME: figure out a principled fix to this issue.
ADMINS = [("Dummy Admin", "dummy@example.com")]


SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
ACCOUNT_DEFAULT_HTTP_PROTOCOL = "https"
CSRF_TRUSTED_ORIGINS = [
    f"https://{os.environ['FQDN']}",
]
USE_X_FORWARDED_HOST = True

STORAGES = {
    "default": {
        "BACKEND": "ynr.storages.MediaStorage",
    },
    "staticfiles": {
        "BACKEND": "ynr.storages.StaticStorage",
    },
}
AWS_STORAGE_BUCKET_NAME = os.environ["S3_MEDIA_BUCKET"]
AWS_S3_REGION_NAME = os.environ["S3_MEDIA_REGION"]
STATICFILES_LOCATION = "static"
MEDIAFILES_LOCATION = "media"
AWS_DEFAULT_ACL = "public-read"
AWS_BUCKET_ACL = AWS_DEFAULT_ACL
AWS_QUERYSTRING_AUTH = False


TEXTRACT_S3_BUCKET_NAME = os.environ["S3_SOPN_BUCKET"]
TEXTRACT_S3_BUCKET_REGION = os.environ["S3_SOPN_REGION"]
TEXTRACT_S3_BUCKET_URL = f"https://{TEXTRACT_S3_BUCKET_NAME}.s3.{TEXTRACT_S3_BUCKET_REGION}.amazonaws.com"


EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
EMAIL_PORT = 587
EMAIL_HOST = os.environ["EMAIL_HOST"]
EMAIL_USE_TLS = True
EMAIL_HOST_USER = os.environ["EMAIL_HOST_USER"]
EMAIL_HOST_PASSWORD = os.environ["EMAIL_HOST_PASSWORD"]
DEFAULT_FROM_EMAIL = os.environ["DEFAULT_FROM_EMAIL"]

SOPN_UPDATE_NOTIFICATION_EMAILS = os.environ[
    "SOPN_UPDATE_NOTIFICATION_EMAILS"
].split(",")


if DC_ENVIRONMENT == "production":
    # TODO: remove this hack and make an ENABLE_SLACK_NOTIFICATIONS setting
    # this exists because we can't set a var to empty string in param store
    SLACK_TOKEN = os.environ["SLACK_TOKEN"]
    if SLACK_TOKEN == "DISABLED":
        SLACK_TOKEN = None
else:
    SLACK_TOKEN = None


ALWAYS_ALLOW_RESULT_RECORDING = True
EDITS_ALLOWED = True

# If set to False, new users won't be allowed to make accounts
# Useful for pre-election anti-vandalism
NEW_USER_ACCOUNT_CREATION_ALLOWED = True


# Sentry config
SENTRY_DSN = os.environ["SENTRY_DSN"]
sentry_sdk.init(
    dsn=SENTRY_DSN,
    integrations=[
        django.DjangoIntegration(),
    ],
    environment=DC_ENVIRONMENT,
    traces_sample_rate=0,
    profiles_sample_rate=0,
)


# AWS X-Ray config
from aws_xray_sdk.core import patch_all, xray_recorder  # noqa: E402

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
MIDDLEWARE.insert(0, "aws_xray_sdk.ext.django.middleware.XRayMiddleware")  # noqa: F405
