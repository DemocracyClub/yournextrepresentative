from django.apps import AppConfig


class PopoloConfig(AppConfig):
    name = "popolo"

    def ready(self):
        import popolo.signals  # noqa
