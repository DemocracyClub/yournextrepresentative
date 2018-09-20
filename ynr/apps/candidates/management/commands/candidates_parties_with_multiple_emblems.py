from django.core.management.base import BaseCommand

from popolo.models import Organization


class Command(BaseCommand):
    def handle(self, *args, **options):

        for party_extra in Organization.objects.filter(
            classification="Party"
        ).prefetch_related("images"):
            images = list(party_extra.images.all())
            if len(images) < 2:
                continue
            print("=====================================================")
            party = party_extra.base
            print(len(images), party_extra.slug, party.name.encode("utf-8"))
            for image in images:
                print("  --")
                print("   " + image.source.encode("utf-8"))
                print("   " + image.image.url)
