import requests
from candidates.management.images import get_image_extension
from django.core.files.base import ContentFile
from django.core.files.temp import NamedTemporaryFile
from django.core.management.base import BaseCommand
from moderation_queue.models import CopyrightOptions, QueuedImage
from people.models import Person

from ..twitter import TwitterAPIData

VERBOSE = False


def verbose(*args, **kwargs):
    if VERBOSE:
        print(*args, **kwargs)


class Command(BaseCommand):
    help = "Add Twitter avatars for candidates without images to the moderation queue"

    def add_twitter_image_to_queue(self, person, image_url, user_id):
        if person.queuedimage_set.exists():
            # Don't add an image to the queue if there is one already
            # in the queue. It doesn't matter if that queued image has
            # been moderated or not, or whether it's been rejected or
            # not. At the moment we just want to be really careful not
            # to make people check the same Twitter avatar twice.
            verbose(
                "  That person already had an image in the queue, so skipping."
            )
            return

        verbose("  Adding that person's Twitter avatar to the moderation queue")
        # Add a new queued image
        image_url = image_url.replace("_normal.", ".")
        img_temp = NamedTemporaryFile(delete=True)
        r = requests.get(image_url)
        if r.status_code != 200:
            msg = (
                "  Ignoring an image URL with non-200 status code "
                "({status_code}): {url}"
            )
            verbose(msg.format(status_code=r.status_code, url=image_url))
            return
        img_temp.write(r.content)
        img_temp.flush()

        # Trying to get the image extension checks that this really is
        # an image:
        if get_image_extension(img_temp.name) is None:
            msg = "  The image at {url} wasn't of a known type"
            verbose(msg.format(url=image_url))
            return

        justification_for_use = (
            "Auto imported from Twitter: "
            "https://twitter.com/intent/user?user_id={user_id}".format(
                user_id=user_id
            )
        )
        qi = QueuedImage(
            decision=QueuedImage.UNDECIDED,
            why_allowed=CopyrightOptions.PROFILE_PHOTO,
            justification_for_use=justification_for_use,
            person=person,
        )
        qi.save()
        qi.image.save(image_url, ContentFile(r.content))
        qi.save()

    def handle_person(self, person):
        twitter_identifiers = person.get_identifiers_of_type("twitter_username")
        for identifier in twitter_identifiers:
            user_id = identifier.internal_identifier

            if user_id and user_id in self.twitter_data.user_id_to_photo_url:
                msg = (
                    "Considering adding a photo for {person} with Twitter "
                    "user ID: {user_id}"
                )
                verbose(msg.format(person=person, user_id=user_id))
                self.add_twitter_image_to_queue(
                    person,
                    self.twitter_data.user_id_to_photo_url[user_id],
                    user_id,
                )

    def handle(self, *args, **options):
        global VERBOSE
        VERBOSE = int(options["verbosity"]) > 1
        self.twitter_data = TwitterAPIData()
        self.twitter_data.update_from_api()
        # Now go through every person in the database and see if we
        # should add their Twitter avatar to the image moderation
        # queue:
        for person in Person.objects.order_by("name"):
            self.handle_person(person)
