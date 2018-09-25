from django.db import models

from people.managers import PersonImageManager


def person_image_path(instance, filename):
    # Ensure the filename isn't too long
    filename = filename[400:]
    # Upload images in a directory per person
    return "images/people/{0}/{1}".format(instance.person.id, filename)


class PersonImage(models.Model):
    """
    Images of people, uploaded by users of the site. It's important we keep
    track of the copyright the uploading user asserts over the image, and any
    notes they have.
    """

    person = models.ForeignKey("popolo.Person", related_name="images")
    image = models.ImageField(upload_to=person_image_path, max_length=512)
    source = models.CharField(max_length=400)
    copyright = models.CharField(max_length=64, default="other", blank=True)
    uploading_user = models.ForeignKey("auth.User", blank=True, null=True)
    user_notes = models.TextField(blank=True)
    md5sum = models.CharField(max_length=32, blank=True)
    user_copyright = models.CharField(max_length=128, blank=True)
    notes = models.TextField(blank=True)
    is_primary = models.BooleanField(default=False)

    objects = PersonImageManager()
