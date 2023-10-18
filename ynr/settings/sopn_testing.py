from .base import *  # noqa
from .base import root

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": "ynr_sopn_testing",
        "USER": "",
        "PASSWORD": "",
    }
}

MEDIA_ROOT = root("media/sopn_testing/")
