from django.core.management.base import BaseCommand

from facebook_data.tasks import save_advert_image
from facebook_data.models import FacebookAdvert


class Command(BaseCommand):
    def handle(self, *args, **options):
        person_ids = (
            FacebookAdvert.objects.filter(image="")
            .order_by("person_id")
            .values_list("person_id", flat=True)
            .distinct()
        )
        for person_id in person_ids:
            ad = FacebookAdvert.objects.filter(
                image="", person_id=person_id
            ).latest()
            save_advert_image.delay(ad.ad_id)
