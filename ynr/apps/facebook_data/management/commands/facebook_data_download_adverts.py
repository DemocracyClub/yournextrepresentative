from django.core.management.base import BaseCommand
from facebook_data.tasks import get_ads_for_page
from people.models import PersonIdentifier


class Command(BaseCommand):
    help = "Import adverts for current candidates from Facebook"

    def handle(self, *args, **options):
        value_types = ["facebook_page_url", "facebook_personal_url"]
        qs = (
            PersonIdentifier.objects.filter(value_type__in=value_types)
            .exclude(internal_identifier=None)
            .filter(person__facebookadvert=None)
            .filter(person__memberships__ballot__election__current=True)
        )

        for identifier in qs:
            get_ads_for_page.delay(
                identifier.person.pk,
                identifier.internal_identifier,
                identifier.value,
            )
