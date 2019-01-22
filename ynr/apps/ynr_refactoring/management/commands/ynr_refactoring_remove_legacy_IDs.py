import json

from django.core.management.base import BaseCommand
from django.db import transaction


from people.models import Person
from candidates.views.version_data import get_change_metadata
from popolo.models import Identifier


class Command(BaseCommand):
    def handle(self, *args, **options):
        schemes = ("yournextmp-candidate", "popit-person")
        # We can't use the GFK any more because we just deleted it, but the
        # content is still there
        identifiers = Identifier.objects.filter(scheme__in=schemes).values_list(
            "object_id", flat=True
        )
        for person in Person.objects.filter(pk__in=identifiers).filter(pk=502):
            with transaction.atomic():
                meta_data = get_change_metadata(
                    None, "Removing legacy identifiers"
                )
                meta_data["username"] = "CandidateBot"

                person.record_version(meta_data)
                person.save()
