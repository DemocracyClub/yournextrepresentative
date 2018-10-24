from datetime import datetime
from random import randint
import sys

from django.core.management.base import BaseCommand
from django.db import transaction

from people.models import Person


class Command(BaseCommand):

    help = "Record the current version for all people"

    def add_arguments(self, parser):
        parser.add_argument(
            "--person-id",
            help="Only record the current version for the person with this ID",
        )
        parser.add_argument(
            "--source", help="The source of information for this other name"
        )

    def handle(self, *args, **options):
        kwargs = {}
        if options["person_id"]:
            kwargs["base__id"] = options["person_id"]
        if options["source"]:
            source = options["source"]
        else:
            source = "New version recorded from the command-line"
        with transaction.atomic():
            for person in Person.objects.filter(**kwargs):
                print(
                    "Recording the current version of {name} ({id})".format(
                        name=person.name, id=person.id
                    ).encode("utf-8")
                )
                person.record_version(
                    {
                        "information_source": source,
                        "version_id": "{:016x}".format(randint(0, sys.maxsize)),
                        "timestamp": datetime.utcnow().isoformat(),
                    }
                )
                person.save()
