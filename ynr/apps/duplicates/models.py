# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models
from django.db.models import Q

from django_extensions.db.models import TimeStampedModel
from model_utils.managers import QueryManager
from model_utils.models import StatusModel
from model_utils import Choices


class PersonExtraQuerySet(models.QuerySet):
    def for_person(self, person):
        return self.for_person_id(person.pk)

    def for_person_id(self, person_id):
        return self.filter(
            Q(person_id=person_id) | Q(other_person_id=person_id)
        )

    def for_both_people(self, person, other_person):
        qs = self.filter(Q(person=person) | Q(person=other_person))
        qs = qs.filter(Q(other_person=other_person) | Q(other_person=person))
        return qs

    def marked_as_not_duplicate(self, person, other_person):
        qs = self.filter(status=self.model.STATUS.not_duplicate)
        qs = qs.for_both_people(person, other_person)
        return qs.exists()


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
        ('suggested', 'Suggested'),
        ('not_duplicate', 'Not duplicate'),
    )

    person = models.ForeignKey(
        'popolo.Person',
        related_name="duplicate_suggestion"
    )
    other_person = models.ForeignKey(
        'popolo.Person',
        related_name="duplicate_suggestion_other_person"
    )
    user = models.ForeignKey('auth.User')


    objects = PersonExtraQuerySet.as_manager()

    class Meta:
        unique_together = ('person', 'other_person')
