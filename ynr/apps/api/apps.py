from django.apps import AppConfig
from django.conf import settings
from django.db.models.signals import post_save


class ApiConfig(AppConfig):
    name = "api"

    def ready(self):
        post_save.connect(create_auth_token, sender=settings.AUTH_USER_MODEL)


def create_auth_token(sender, instance=None, created=False, **kwargs):
    if created:
        from rest_framework.authtoken.models import Token

        Token.objects.create(user=instance)
