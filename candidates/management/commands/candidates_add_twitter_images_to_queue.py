from __future__ import print_function, unicode_literals

from django.core.files.temp import NamedTemporaryFile
from django.core.files import File
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils.translation import ugettext as _

from candidates.models import MultipleTwitterIdentifiers
from moderation_queue.models import QueuedImage, CopyrightOptions
from popolo.models import Person

import requests

from ..twitter import TwitterAPIData


VERBOSE = False


def verbose(*args, **kwargs):
    if VERBOSE:
        print(*args, **kwargs)


class Command(BaseCommand):

    help = "Add Twitter avatars for candidates without images to the moderation queue"

    def add_twitter_image_to_queue(self, person, image_url):
        if person.queuedimage_set.exclude(decision="rejected").exists():
            # Don't add an image to the queue if there is one already
            # Ignoring rejected queued images
            verbose(_("  That person already had in image, so skipping."))
            return

        verbose(_("  Adding that person's Twitter avatar to the moderation queue"))
        # Add a new queued image
        image_url = image_url.replace('_normal.', '.')
        img_temp = NamedTemporaryFile(delete=True)
        img_temp.write(requests.get(image_url).content)
        img_temp.flush()

        qi = QueuedImage(
            decision=QueuedImage.UNDECIDED,
            why_allowed=CopyrightOptions.PROFILE_PHOTO,
            justification_for_use="Auto imported from Twitter",
            person=person
        )
        qi.save()
        qi.image.save(image_url, File(img_temp))
        qi.save()

    def handle_person(self, person):
        try:
            user_id, screen_name = person.extra.twitter_identifiers
        except MultipleTwitterIdentifiers as e:
            print(u"WARNING: {message}, skipping".format(message=e))
            return
        if user_id and user_id in self.twitter_data.user_id_to_photo_url:
            msg = "Considering adding a photo for {person} with Twitter " \
                  "user ID: {user_id}"
            verbose(_(msg).format(person=person, user_id=user_id))
            self.add_twitter_image_to_queue(
                person, self.twitter_data.user_id_to_photo_url[user_id])

    def handle(self, *args, **options):
        global VERBOSE
        VERBOSE = int(options['verbosity']) > 1
        self.twitter_data = TwitterAPIData()
        self.twitter_data.update_from_api()
        # Now go through every person in the database and see if we
        # should add their Twitter avatar to the image moderation
        # queue:
        for person in Person.objects.select_related('extra'):
            with transaction.atomic():
                self.handle_person(person)
