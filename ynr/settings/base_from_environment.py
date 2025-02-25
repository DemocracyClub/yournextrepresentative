import os

SECRET_KEY = os.environ["YNR_DJANGO_SECRET_KEY"]
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "HOST": os.environ["YNR_POSTGRES_HOSTNAME"],
        "NAME": os.environ["YNR_POSTGRES_DATABASE"],
        "USER": os.environ["YNR_POSTGRES_USERNAME"],
        "PASSWORD": os.environ["YNR_POSTGRES_PASSWORD"],
        "OPTIONS": {"sslmode": "require"},
    }
}
