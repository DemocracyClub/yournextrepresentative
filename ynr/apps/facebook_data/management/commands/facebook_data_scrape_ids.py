from django.core.management.base import BaseCommand

from facebook_data.tasks import extract_fb_page_id
from people.models import PersonIdentifier


class Command(BaseCommand):
    def handle(self, *args, **options):
        value_types = ["facebook_page_url", "facebook_personal_url"]
        qs = PersonIdentifier.objects.filter(
            value_type__in=value_types, internal_identifier=None
        ).filter(person__memberships__ballot__election__current=True)

        for identifier in qs:
            extract_fb_page_id.delay(identifier.pk)
