from os.path import join

from django.db import models
from django.core.files.storage import DefaultStorage
from django.conf import settings

from ynr_refactoring.settings import PersonIdentifierFields


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


class PersonIdentifierQuerySet(models.query.QuerySet):
    def select_choices(self):
        default_option = [(None, "")]
        options = [(f.name, f.value) for f in PersonIdentifierFields]
        return default_option + options


class PersonQuerySet(models.query.QuerySet):
    def missing(self, field):
        people_in_current_elections = self.filter(
            memberships__post_election__election__current=True
        )
        # The field can be one of several types:
        simple_field = [
            f for f in settings.SIMPLE_POPOLO_FIELDS if f.name == field
        ]
        if simple_field:
            return people_in_current_elections.filter(**{field: ""})

        if hasattr(PersonIdentifierFields, field):
            return people_in_current_elections.exclude(
                tmp_person_identifiers__value_type=field
            )

        # If we get to this point, it's a non-existent field on the person:
        raise ValueError("Unknown field '{}'".format(field))

    def joins_for_csv_output(self):
        from popolo.models import Membership

        return self.prefetch_related(
            models.Prefetch(
                "memberships",
                Membership.objects.select_related(
                    "post_election", "post_election__election", "party", "post"
                ),
            ),
            "identifiers",
            "links",
            "images__uploading_user",
            "tmp_person_identifiers",
        )
