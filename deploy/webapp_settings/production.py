# Only set this to True in development environments
from datetime import date

from .base import *  # noqa

DEBUG = False
CAN_EDIT_ELECTIONS = False

# Set this to a long random string and keep it secret
# This is a handy tool:
# https://www.miniwebtool.com/django-secret-key-generator/
SECRET_KEY = "{{ production_django_secret_key }}"
MEDIA_ROOT = "{{ django_media_root }}"

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql_psycopg2",
        "NAME": "{{project_name}}",
        "USER": "{{postgres_username}}",
        "PASSWORD": "{{postgres_password}}",
        "HOST": "{{postgres_host}}",
    },
}

# A list of tuples containing (Full name, email address)
ADMINS = [("YNR Prod Developers", "developers+ynr-prod@democracyclub.org.uk")]

CELERY_BROKER_URL = "redis://localhost:6379/0"

SITE_WIDE_MESSAGES = [
    {
        "message": """
            Election data parties! Join us on the 10th of April in London,
            Birmingham or Manchester for one of our famous SOPN parties!
        """,
        "show_until": "2018-04-10T18:00",
        "url": "https://democracyclub.org.uk/blog/2018/03/29/election-data-parties/",
    }
]


# **** Other settings that might be useful to change locally

ALLOWED_HOSTS = ["*"]
INTERNAL_IPS = [
    "127.0.0.1",
    "localhost",
]

CACHES = {
    "default": {
        "TIMEOUT": None,  # cache keys never expire; we invalidate them
        "BACKEND": "django.core.cache.backends.memcached.PyMemcacheCache",
        "LOCATION": "127.0.0.1:11211",
        "KEY_PREFIX": DATABASES["default"]["NAME"],
    },
    "thumbnails": {
        "TIMEOUT": 60 * 60 * 24 * 2,  # expire after two days
        "BACKEND": "django.core.cache.backends.memcached.PyMemcacheCache",
        "LOCATION": "127.0.0.1:11211",
        "KEY_PREFIX": DATABASES["default"]["NAME"] + "-thumbnails",
    },
}


# **** Settings that might be useful in production

TWITTER_APP_ONLY_BEARER_TOKEN = "{{TWITTER_APP_ONLY_BEARER_TOKEN}}"
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
ACCOUNT_DEFAULT_HTTP_PROTOCOL = "https"
RAVEN_CONFIG = {"dsn": "{{RAVEN_DSN}}"}

RUNNING_TESTS = False


# This should be one of:
# ELECTION_STATS
# SOPN_TRACKER
# RESULTS_PROGRESS
# BY_ELECTIONS
FRONT_PAGE_CTA = "BY_ELECTIONS"
SOPN_TRACKER_INFO = {}
SOPN_TRACKER_INFO["election_date"] = "2022-05-05"
SOPN_TRACKER_INFO["election_name"] = "May 2022 local elections"
SOPN_SHEET_URL = "https://docs.google.com/spreadsheets/d/1eyYvkHqvpmowxvpJ3gALfDtPXfJF7nqvMt1ttxLa9fM/edit#gid=0"
SOPN_DATES = [
    ("Scotland", date(year=2022, month=3, day=30)),
    ("England and Wales", date(year=2022, month=4, day=6)),
    ("Northern Ireland", date(year=2022, month=4, day=8)),
]


SCHEDULED_ELECTION_DATES = ["2022-05-06"]


STATICFILES_STORAGE = "ynr.storages.StaticStorage"
DEFAULT_FILE_STORAGE = "ynr.storages.MediaStorage"
AWS_STORAGE_BUCKET_NAME = "static-candidates.democracyclub.org.uk"
AWS_S3_REGION_NAME = "eu-west-2"
STATICFILES_LOCATION = "static"
MEDIAFILES_LOCATION = "media"
AWS_DEFAULT_ACL = "public-read"
AWS_BUCKET_ACL = AWS_DEFAULT_ACL


CSRF_TRUSTED_ORIGINS = [
    "https://{{ domain }}",
]

USE_X_FORWARDED_HOST = True

EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
EMAIL_PORT = 587
EMAIL_HOST = "email-smtp.eu-west-1.amazonaws.com"
EMAIL_USE_TLS = True
EMAIL_HOST_USER = "{{smtp_username}}"
EMAIL_HOST_PASSWORD = "{{smtp_password}}"


#  Send errors to sentry by default
LOGGING["handlers"]["sentry"] = {  # noqa
    "level": "WARNING",
    "class": "raven.contrib.django.raven_compat.handlers.SentryHandler",
}
# LOGGING["loggers"]["account_adapter"]: {
#     'level': 'WARNING',
#     'handlers': ['sentry'],
#     'propagate': False,
# }


SLACK_TOKEN = "{{slack_token}}"

CELERY_IMPORTS = [
    "ynr.apps.sopn_parsing.tasks",
]
ALWAYS_ALLOW_RESULT_RECORDING = True
FF_COOKIE_PATH = "/var/www/ynr/cookies.sqlite"
FACEBOOK_TOKEN = "EAAHFkAGrkL8BAEDkR3PMZBYBhNKTcxrejQQm3cpfkpApT9BhenJmqkzgTeCYDNSkY2nZBDoPo1ztaOKsf8EKCHpsel8dasjJxua1dS0XIlZBBlIgpovpwY6S1hGXStM6tlK78OF6hr4owcZAZAcZA3WS2dHG6CGNIEuEEqFpLCHkB9WaT56HWt"


EDITS_ALLOWED = True
