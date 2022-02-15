from datetime import datetime

from django.db import models
from django.db.models import Q

from utils.db import LastWord

__author__ = "guglielmo"


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


class OrganizationQuerySet(DateframeableQuerySet):
    pass


class PostQuerySet(DateframeableQuerySet):
    pass


class MembershipQuerySet(DateframeableQuerySet):
    def for_csv(self):

        return (
            self.select_related(
                "ballot",
                "ballot__election",
                "ballot__post",
                "person",
                "person__image",
                "person__image__uploading_user",
                "party",
                "ballot__post__organization",
            )
            .prefetch_related("person__tmp_person_identifiers")
            .order_by(
                "ballot__election__election_date",
                "-ballot__election__slug",
                "person__pk",
            )
        )

    def memberships_for_ballot(
        self, ballot, exclude_memberships_qs=None, exclude_people_qs=None
    ):
        elected_ordering = models.F("elected").desc(nulls_last=True)
        order_by = [elected_ordering, "-result__num_ballots"]
        if ballot.election.party_lists_in_use:
            order_by += ["party__name", "party_list_position"]
        else:
            order_by += ["person__sort_name", "last_name"]

        qs = self.filter(ballot=ballot)
        qs = qs.annotate(last_name=LastWord("person__name"))
        qs = qs.order_by(*order_by)
        qs = qs.select_related("person", "person__image", "party", "result")

        if exclude_memberships_qs and exclude_memberships_qs.exists():
            qs = qs.exclude(
                person__pk__in=exclude_memberships_qs.values("person__pk")
            )

        if exclude_people_qs and exclude_people_qs.exists():
            qs = qs.exclude(person__pk__in=exclude_people_qs)

        return qs


class ContactDetailQuerySet(DateframeableQuerySet):
    pass


class OtherNameQuerySet(DateframeableQuerySet):
    pass
