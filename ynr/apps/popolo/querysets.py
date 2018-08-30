from django.conf import settings
from django.db.models import Q

from candidates.models import (
    ComplexPopoloField,
    ExtraField,
    PersonExtraFieldValue,
)

__author__ = "guglielmo"

from django.db import models
from datetime import datetime


class DateframeableQuerySet(models.query.QuerySet):
    """
    A custom ``QuerySet`` allowing easy retrieval of current, past and future instances
    of a Dateframeable model.

    Here, a *Dateframeable model* denotes a model class having an associated date range.

    We assume that the date range is described by two ``Char`` fields
    named ``start_date`` and ``end_date``, respectively,
    whose validation pattern is: "^[0-9]{4}(-[0-9]{2}){0,2}$",
    in order to represent partial dates.
    """

    def past(self, moment=None):
        """
        Return a QuerySet containing the *past* instances of the model
        (i.e. those having an end date which is in the past).
        """
        if moment is None:
            moment = datetime.strftime(datetime.now(), "%Y-%m-%d")
        return self.filter(end_date__lte=moment)

    def future(self, moment=None):
        """
        Return a QuerySet containing the *future* instances of the model
        (i.e. those having a start date which is in the future).
        """
        if moment is None:
            moment = datetime.strftime(datetime.now(), "%Y-%m-%d")
        return self.filter(start_date__gte=moment)

    def current(self, moment=None):
        """
        Return a QuerySet containing the *current* instances of the model
        at the given moment in time, if the parameter is spcified
        now if it is not
        @moment - is a string, representing a date in the YYYY-MM-DD format
        (i.e. those for which the moment date-time lies within their associated time range).
        """
        if moment is None:
            moment = datetime.strftime(datetime.now(), "%Y-%m-%d")

        return self.filter(
            Q(start_date__lte=moment)
            & (Q(end_date__gte=moment) | Q(end_date__isnull=True))
        )


class PersonQuerySet(DateframeableQuerySet):
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
        complex_field = ComplexPopoloField.objects.filter(name=field).first()
        if complex_field:
            kwargs = {
                "{relation}__{key}".format(
                    relation=complex_field.popolo_array,
                    key=complex_field.info_type_key,
                ): complex_field.info_type
            }
            return people_in_current_elections.exclude(**kwargs)
        extra_field = ExtraField.objects.filter(key=field).first()
        if extra_field:
            # This case is a bit more complicated because the
            # PersonExtraFieldValue class allows a blank value.
            pefv_completed = PersonExtraFieldValue.objects.filter(
                field=extra_field
            ).exclude(value="")
            return people_in_current_elections.exclude(
                id__in=[pefv.person_id for pefv in pefv_completed]
            )
        # If we get to this point, it's a non-existent field on the person:
        raise ValueError("Unknown field '{}'".format(field))

    def joins_for_csv_output(self):
        from popolo.models import Membership

        return self.prefetch_related(
            models.Prefetch(
                "memberships",
                Membership.objects.select_related(
                    "post_election__election",
                    "on_behalf_of__extra",
                    "post__area",
                    "post",
                ).prefetch_related(
                    "on_behalf_of__identifiers", "post__area__other_identifiers"
                ),
            ),
            "contact_details",
            "identifiers",
            "links",
            "images__extra__uploading_user",
            models.Prefetch(
                "extra_field_values",
                PersonExtraFieldValue.objects.select_related("field"),
            ),
        )


class OrganizationQuerySet(DateframeableQuerySet):
    pass


class PostQuerySet(DateframeableQuerySet):
    pass


class MembershipQuerySet(DateframeableQuerySet):
    pass


class ContactDetailQuerySet(DateframeableQuerySet):
    pass


class OtherNameQuerySet(DateframeableQuerySet):
    pass
