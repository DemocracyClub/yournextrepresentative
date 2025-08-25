# TODO: remove this import. Importing from the base module recognises the large
# number of settings it configures, and our desire not to put their transfer
# into this module on the critical path.
import os

from .base import *  # noqa

INTERNAL_IPS = [
    "127.0.0.1",
    "localhost",
]

SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
ACCOUNT_DEFAULT_HTTP_PROTOCOL = "https"
CSRF_TRUSTED_ORIGINS = [
    f"https://{os.environ.get('FQDN')}",
]
USE_X_FORWARDED_HOST = True

RUNNING_TESTS = False

SECRET_KEY = os.environ["DJANGO_SECRET_KEY"]


# In an AWS-ECS-behind-ALB context, the ALB's health checks don't yet arrive
# with a meaningful HTTP host header. We currently rely on the ALB to route
# only appropriate requests to the webapp, and can therefore nullify Django's
# protections as they no longer apply in any environment that imports this
# module.
ALLOWED_HOSTS = ["*"]


STATICFILES_STORAGE = "ynr.storages.StaticStorage"
DEFAULT_FILE_STORAGE = "ynr.storages.MediaStorage"
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
EMAIL_HOST = "email-smtp.eu-west-2.amazonaws.com"
EMAIL_USE_TLS = True
EMAIL_HOST_USER = "TODO"  # TODO os.environ["SMTP_USERNAME"]
EMAIL_HOST_PASSWORD = "TODO"  # TODO os.environ["SMTP_PASSWORD"]

if DC_ENVIRONMENT == "production":  # noqa: F405
    SLACK_TOKEN = os.environ["SLACK_TOKEN"]
else:
    SLACK_TOKEN = None

ALWAYS_ALLOW_RESULT_RECORDING = True
EDITS_ALLOWED = True

# If set to False, new users won't be allowed to make accounts
# Useful for pre-election anti-vandalism
NEW_USER_ACCOUNT_CREATION_ALLOWED = True
