import importlib

from django.apps import AppConfig
from django.conf import settings
from django.db import connection
from django.db.models.signals import post_migrate


def create_materialized_view_when_migrations_disabled(**kwargs):
    """
    This is needed because we manage the view in a migration (to better allow changing
    it over time), but we disable migrations when running tests.

    Parts of the application relies on the view existing, so we need to ensure it's there
    by using a `post_migrate` signal (that's called even when no migrations are run)

    """
    if settings.MIGRATION_MODULES.__class__.__name__ == "DisableMigrations":
        migration = importlib.import_module(
            "data_exports.migrations.0002_create_sql", package=None
        )

        with connection.cursor() as cursor:
            cursor.execute(migration.SQL_STR)


class DataExportsConfig(AppConfig):
    name = "data_exports"

    def ready(self):
        post_migrate.connect(
            create_materialized_view_when_migrations_disabled, sender=self
        )
