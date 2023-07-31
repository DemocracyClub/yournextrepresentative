from django.core.management.base import BaseCommand
from people.models import Person


class Command(BaseCommand):
    help = "Update the vector search field on the Person model"

    def handle(self, *args, **options):
        Person.objects.update_name_search_trigger()
        Person.objects.update_name_search()
