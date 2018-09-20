import re
from os.path import join

from django.db import models
from django.core.files.storage import DefaultStorage


class PersonImageManager(models.Manager):
    def create_from_file(self, image_filename, ideal_relative_name, defaults):
        # Import the file to media root and create the ORM
        # objects.
        storage = DefaultStorage()
        desired_storage_path = join("images", ideal_relative_name)
        with open(image_filename, "rb") as f:
            storage_filename = storage.save(desired_storage_path, f)
        return self.create(image=storage_filename, **defaults)

    def update_or_create_from_file(
        self, image_filename, ideal_relative_name, person, defaults
    ):
        try:
            image = self.get(person=person, md5sum=defaults["md5sum"])
            for k, v in defaults.items():
                setattr(image, k, v)
            image.save()
            return image, False

        except self.model.DoesNotExist:
            # Prepare args for the base object first:
            defaults["person"] = person

            # And now the extra object:
            image = self.create_from_file(
                image_filename, ideal_relative_name, defaults
            )
        return image
