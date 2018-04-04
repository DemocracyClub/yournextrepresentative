from .base import *  # noqa


DATABASES['default']['CONN_MAX_AGE'] = 0
SITE_NAME = "example.com"

CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.dummy.DummyCache',
    }
}


PASSWORD_HASHERS = [
    'django.contrib.auth.hashers.MD5PasswordHasher',
]

RUNNING_TESTS = True

# Normally we use CelerySignalProcessor, however this makes testing harder,
# as (rightly), the celery tasks wait until a transation has been committed
# before indexing. This causes problems with tests, as they all run in a
# transaction. We could use TransactionTestCase, but that would have to be
# used almost everywhere, and would cause more problems. This is a simplier
# method, and ultimatlly the value in testing celery with `CELERY_ALWAYS_EAGER`
# isn't much, as it's not the same as prod anyway.
HAYSTACK_SIGNAL_PROCESSOR = 'haystack.signals.RealtimeSignalProcessor'


SECRET_KEY = "just here for testing"

if os.environ.get('TRAVIS'):
    try:
        from .travis import *  # noqa
    except ImportError:
        pass
