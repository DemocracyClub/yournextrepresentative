from data_exports.models import MaterializedMemberships
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Updates the MaterializedMemberships materialized view"

    def handle(self, *args, **options):
        MaterializedMemberships.refresh_view()
