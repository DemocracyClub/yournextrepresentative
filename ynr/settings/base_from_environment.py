# TODO: remove this import. Importing from the base module recognises the large
# number of settings it configures, and our desire not to put their transfer
# into this module on the critical path.
import os

from .base import *  # noqa

SECRET_KEY = os.environ["YNR_DJANGO_SECRET_KEY"]
#DATABASES = {
#    "default": {
#        "ENGINE": "django.db.backends.postgresql",
#        "HOST": os.environ["YNR_POSTGRES_HOSTNAME"],
#        "NAME": os.environ["YNR_POSTGRES_DATABASE"],
#        "USER": os.environ["YNR_POSTGRES_USERNAME"],
#        "PASSWORD": os.environ["YNR_POSTGRES_PASSWORD"],
#        "OPTIONS": {"sslmode": "require"},
#    }
#}

# In an AWS-ECS-behind-ALB context, the ALB's health checks don't yet arrive
# with a meaningful HTTP host header. We currently rely on the ALB to route
# only appropriate requests to the webapp, and can therefore nullify Django's
# protections as they no longer apply in any environment that imports this
# module.
ALLOWED_HOSTS = ['*']

AWS_STORAGE_BUCKET_NAME = os.environ["YNR_AWS_S3_MEDIA_BUCKET"]
AWS_S3_REGION_NAME = os.environ["YNR_AWS_S3_MEDIA_REGION"]

TEXTRACT_S3_BUCKET_NAME = os.environ["YNR_AWS_S3_SOPN_BUCKET"]
TEXTRACT_S3_BUCKET_REGION = os.environ["YNR_AWS_S3_SOPN_REGION"]
TEXTRACT_S3_BUCKET_URL = f"https://{TEXTRACT_S3_BUCKET_NAME}.s3.{TEXTRACT_S3_BUCKET_REGION}.amazonaws.com"
