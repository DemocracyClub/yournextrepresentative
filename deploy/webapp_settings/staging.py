# Only set this to True in development environments
DEBUG = True

# Set this to a long random string and keep it secret
# This is a handy tool:
# https://www.miniwebtool.com/django-secret-key-generator/
SECRET_KEY = "{{ staging_django_secret_key }}"
MEDIA_ROOT = "{{ django_media_root }}"
STATICFILES_DIRS = ()

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": "{{project_name}}",
        "USER": "{{project_name}}",
        "PASSWORD": "",
    },
}

# A tuple of tuples containing (Full name, email address)
ADMINS = ("YNR Stage Developers", "developers+ynr-stage@democracyclub.org.uk")

# **** Other settings that might be useful to change locally

ALLOWED_HOSTS = ["*"]
INTERNAL_IPS = [
    "127.0.0.1",
    "localhost",
]

# CACHES = {
#     "default": {
#         "BACKEND": "django.core.cache.backends.dummy.DummyCache",
#     }
# }


# **** Settings that might be useful in production

STATICFILES_STORAGE = "pipeline.storage.PipelineCachedStorage"
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
ACCOUNT_DEFAULT_HTTP_PROTOCOL = "https"
# RAVEN_CONFIG = {
#     'dsn': ''
# }
