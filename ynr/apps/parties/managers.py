import re

from django.db import models
from django.utils import timezone
from django.utils.functional import cached_property

from .constants import JOINT_DESCRIPTION_REGEX


class PartyQuerySet(models.QuerySet):
    def active_for_date(self, date=None):
        if not date:
            date = timezone.now()
        qs = self.filter(date_registered__lte=date)
        qs = qs.filter(
            models.Q(date_deregistered__gte=date)
            | models.Q(date_deregistered=None)
        )
        return qs

    def current(self):
        return self.active_for_date()

    def register(self, register):
        register = register.upper()
        return self.filter(
            models.Q(register=register) | models.Q(register=None)
        )

    def order_by_memberships(self, date=None, nocounts=False):
        qs = self
        if date:
            qs = qs.filter(membership__ballot__election__election_date=date)
            qs = qs.annotate(
                candidate_count=models.Count("membership")
            ).order_by("-candidate_count", "name")

        if nocounts:
            qs = qs.filter(
                ~models.Q(membership__ballot__election__election_date=date)
            ).annotate(candidate_count=models.Value(0, models.IntegerField()))

        return qs

    def party_choices(
        self,
        include_descriptions=True,
        exclude_deregistered=False,
        include_description_ids=False,
        include_non_current=True,
    ):
        # For various reasons, we've found it's best to order the
        # parties by those that have the most candidates - this means
        # that the commonest parties to select are at the top of the
        # drop down.  The logic here tries to build such an ordered
        # list of candidates if there are enough that such an ordering
        # makes sense.  Otherwise the fallback is to rank
        # alphabetically.

        party_filter_kwargs = {}
        party_order_by = ["name"]
        if include_non_current:
            party_order_by.insert(0, "-total_candidates")
        else:
            party_filter_kwargs["current_candidates__gt"] = 0
            party_order_by.insert(0, "-current_candidates")

        parties_current_qs = (
            self.filter(**party_filter_kwargs)
            .order_by(*party_order_by)
            .only("date_deregistered", "name", "ec_id")
        )

        if include_descriptions:
            parties_current_qs = parties_current_qs.prefetch_related(
                "descriptions"
            )

        result = [("", "")]

        for party in parties_current_qs:

            if party.date_deregistered:
                if party.is_deregistered and exclude_deregistered:
                    continue
            if include_descriptions and party.descriptions.exists():
                names = [(party.ec_id, party.format_name)]
                for description in party.descriptions.all():
                    joint_text = re.compile(JOINT_DESCRIPTION_REGEX, re.I)
                    party_id_str = str(party.ec_id)
                    if include_description_ids:
                        party_id_str = "{}__{}".format(
                            party_id_str, description.pk
                        )
                    if not joint_text.search(description.description):
                        names.append((party_id_str, description.description))
                party_names = (party.format_name, names)
            else:
                party_names = (str(party.ec_id), party.format_name)

            result.append(party_names)
        return result

    def default_party_choices(self):
        return self.party_choices(
            include_descriptions=True,
            include_non_current=False,
            exclude_deregistered=True,
        )
