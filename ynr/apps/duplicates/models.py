# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models
from django.db.models import Q

from django_extensions.db.models import TimeStampedModel
from model_utils.models import StatusModel
from model_utils import Choices


def sort_people(person_a, person_b):
    return sorted([person_a, person_b], key=lambda m: m.pk)


class DuplicateSuggestionQuerySet(models.QuerySet):
    def for_person(self, person):
        return self.for_person_id(person.pk)

    def for_person_id(self, person_id):
        return self.filter(
            Q(person_id=person_id) | Q(other_person_id=person_id)
        )

    def for_both_people(self, person, other_person):
        person, other_person = sort_people(person, other_person)
        qs = self.filter(person=person, other_person=other_person)
        return qs

    def marked_as_not_duplicate(self, person, other_person):
        qs = self.filter(status=self.model.STATUS.not_duplicate)
        qs = qs.for_both_people(person, other_person)
        return qs.exists()

    def get_or_create(self, defaults=None, **kwargs):
        kwargs["person"], kwargs["other_person"] = sort_people(
            kwargs["person"], kwargs["other_person"]
        )
        return super().get_or_create(defaults, **kwargs)

    def update_or_create(self, defaults=None, **kwargs):
        kwargs["person"], kwargs["other_person"] = sort_people(
            kwargs["person"], kwargs["other_person"]
        )
        return super().update_or_create(defaults, **kwargs)


class DuplicateSuggestion(StatusModel, TimeStampedModel):
    """
    A model for storing duplicate suggestions.

    TODO:

    * If a person has N duplicate suggestions and one gets merged in to the
      other, what do we do?
    * Mark people known as not duplicate in a KnownNotDuplicateQuerySet –
      this prevents people from marking someone as a duplicate when it's known
      they are not (for example, because they've been suggested before)
    """

    STATUS = Choices(
        ("suggested", "Suggested"), ("not_duplicate", "Not duplicate")
    )

    person = models.ForeignKey(
        "people.Person",
        related_name="duplicate_suggestion",
        on_delete=models.CASCADE,
    )
    other_person = models.ForeignKey(
        "people.Person",
        related_name="duplicate_suggestion_other_person",
        on_delete=models.CASCADE,
    )
    user = models.ForeignKey("auth.User", on_delete=models.CASCADE)

    objects = DuplicateSuggestionQuerySet.as_manager()

    class Meta:
        unique_together = ("person", "other_person")

    def save(self, **kwargs):
        """
        Force the order of the IDs, making self.person always
        the lower of the two IDs
        """

        self.person, self.other_person = sort_people(
            self.person, self.other_person
        )
        assert self.person.pk < self.other_person.pk

        return super().save(**kwargs)
