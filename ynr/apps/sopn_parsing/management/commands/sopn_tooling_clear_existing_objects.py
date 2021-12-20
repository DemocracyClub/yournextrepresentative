from django.conf import settings
from bulk_adding.models import RawPeople
from django.core.management.base import BaseCommand

from official_documents.models import OfficialDocument


class Command(BaseCommand):
    """
    Used to quickly delete existing objects used when testing SOPN
    parsing so that you can start fresh for example, when you want
    to start testing a new set of SOPNs.
    """

    def print_deleted(self, deleted_dict):
        for object, count in deleted_dict.items():
            self.stdout.write(f"Deleted {count} {object}")

    def handle(self, *args, **options):
        if settings.SETTINGS_MODULE != "ynr.settings.sopn_testing":
            raise ValueError(
                "You are trying to run this command outside of SOPN testing environment"
            )

        deleted_dict = {}
        deleted_dict.update(OfficialDocument.objects.all().delete()[1])
        deleted_dict.update(RawPeople.objects.all().delete()[1])
        self.print_deleted(deleted_dict)
