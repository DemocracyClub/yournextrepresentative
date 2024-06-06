# Only set this to True in development environments
import os
from datetime import date

import requests

from .base import *  # noqa

MEDIA_ROOT = "{{ django_media_root }}"

try:
    EC2_IP = requests.get(
        "http://169.254.169.254/latest/meta-data/local-ipv4", timeout=2
    ).text
    ALLOWED_HOSTS.append(EC2_IP)  # noqa
except requests.exceptions.RequestException:
    pass

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

INTERNAL_IPS = [
    "127.0.0.1",
    "localhost",
]

CACHES = {
    "default": {
        "TIMEOUT": None,  # cache keys never expire; we invalidate them
        "BACKEND": "django.core.cache.backends.memcached.PyMemcacheCache",
        "LOCATION": "127.0.0.1:11211",
        "KEY_PREFIX": DATABASES["default"]["NAME"],  # noqa
    },
    "thumbnails": {
        "TIMEOUT": 60 * 60 * 24 * 2,  # expire after two days
        "BACKEND": "django.core.cache.backends.memcached.PyMemcacheCache",
        "LOCATION": "127.0.0.1:11211",
        "KEY_PREFIX": DATABASES["default"]["NAME"] + "-thumbnails",  # noqa
    },
}

# **** Settings that might be useful in production
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
ACCOUNT_DEFAULT_HTTP_PROTOCOL = "https"
RAVEN_CONFIG = {"dsn": os.environ.get("RAVEN_DSN")}

RUNNING_TESTS = False

# This should be one of:
# ELECTION_STATS
# SOPN_TRACKER
# RESULTS_PROGRESS
# DATA_DOWNLOAD
# BY_ELECTIONS
FRONT_PAGE_CTA = "SOPN_TRACKER"
SOPN_TRACKER_INFO = {
    "election_date": "2024-07-04",
    "election_name": "2024 general election",
}
SOPN_SHEET_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vRnjgy1HCQBHtQovwRNuoVA3-jVcGluRvlKFx0ad5IjXEB9PjHQPr-8DqzvqYb9EjF7OwMGtq8uHGnF/pub?output=csv"
SOPN_DATES = [
    # ("Scotland", date(year=2023, month=3, day=30)),
    # ("England and Wales", date(year=2024, month=4, day=5)),
    # ("Northern Ireland", date(year=2023, month=4, day=24)),
    ("Great Britain", date(year=2024, month=6, day=7)),
]

DATA_DOWNLOAD_INFO = {
    "election_date": "2024-07-04",
    "election_name": "2024 general election",
    "election_regex": "parl.2024-07-04",
}

SCHEDULED_ELECTION_DATES = ["2024-07-04"]

STATICFILES_STORAGE = "ynr.storages.StaticStorage"
DEFAULT_FILE_STORAGE = "ynr.storages.MediaStorage"
AWS_STORAGE_BUCKET_NAME = "static-candidates.democracyclub.org.uk"
AWS_S3_REGION_NAME = "eu-west-2"
STATICFILES_LOCATION = "static"
MEDIAFILES_LOCATION = "media"
AWS_DEFAULT_ACL = "public-read"
AWS_BUCKET_ACL = AWS_DEFAULT_ACL
AWS_QUERYSTRING_AUTH = False

CSRF_TRUSTED_ORIGINS = [
    f"https://{os.environ.get('FQDN')}",
]

USE_X_FORWARDED_HOST = True

EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
EMAIL_PORT = 587
EMAIL_HOST = "email-smtp.eu-west-1.amazonaws.com"
EMAIL_USE_TLS = True
EMAIL_HOST_USER = os.environ.get("SMTP_USERNAME")
EMAIL_HOST_PASSWORD = os.environ.get("SMTP_PASSWORD")

SLACK_TOKEN = os.environ.get("SLACK_TOKEN")

CELERY_IMPORTS = [
    "ynr.apps.sopn_parsing.tasks",
]
ALWAYS_ALLOW_RESULT_RECORDING = True
EDITS_ALLOWED = True
