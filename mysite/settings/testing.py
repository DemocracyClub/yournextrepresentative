from .base import *  # noqa


DATABASES['default']['CONN_MAX_AGE'] = 0

CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.dummy.DummyCache',
    }
}


PASSWORD_HASHERS = [
    'django.contrib.auth.hashers.MD5PasswordHasher',
]

RUNNING_TESTS = True

SECRET_KEY = "just here for testing"

if os.environ.get('TRAVIS'):
    try:
        from .travis import *  # noqa
    except ImportError:
        pass
