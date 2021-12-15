from .base import root
from .base import *  # noqa

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql_psycopg2",
        "NAME": "ynr_sopn_testing",
        "USER": "",
        "PASSWORD": "",
    }
}

MEDIA_ROOT = root("media/sopn_testing/")
