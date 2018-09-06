from datetime import date
import re

from dateutil import parser

from django.utils import timezone
from django.db import models
from django.conf import settings

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
        return self.filter(register=register)

    def order_by_memberships(self, date=None, nocounts=False):
        qs = self
        if date:
            qs = qs.filter(
                membership__post_election__election__election_date=date
            )
            qs = qs.annotate(
                candidate_count=models.Count("membership")
            ).order_by("-candidate_count", "name")

        if nocounts:
            qs = qs.filter(
                ~models.Q(
                    membership__post_election__election__election_date=date
                )
            ).annotate(candidate_count=models.Value(0, models.IntegerField()))

        return qs

    def party_choices_basic(self):
        result = list(self.order_by("name").values_list("ec_id", "name"))
        result.insert(0, ("", ""))
        return result

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
        from popolo.models import Membership

        candidacies_ever_qs = (
            self.annotate(candidate_count=models.Count("membership")).order_by(
                "-candidate_count", "name"
            )
            # .only("end_date", "name")
        )

        parties_current_qs = (
            self.filter(membership__post_election__election__current=True)
            .annotate(candidate_count=models.Count("membership"))
            .order_by("-candidate_count", "name")
            # .only("end_date", "name")
        )

        if not include_non_current:
            parties_current_qs = parties_current_qs.exclude(candidate_count=0)

        parties_notcurrent_qs = (
            self.filter(
                ~models.Q(membership__post_election__election__current=True)
            )
            .annotate(candidate_count=models.Value(0, models.IntegerField()))
            .order_by("-candidate_count", "name")
            # .only("end_date", "name")
        )

        minimum_count = settings.CANDIDATES_REQUIRED_FOR_WEIGHTED_PARTY_LIST

        total_memberships = Membership.objects.all()
        current_memberships = total_memberships.filter(
            post_election__election__current=True
        )

        queries = []
        if current_memberships.count() > minimum_count:
            queries.append(parties_current_qs)
            if include_non_current:
                queries.append(parties_notcurrent_qs)
        elif total_memberships.count() > minimum_count:
            queries.append(candidacies_ever_qs)
        else:
            return self.party_choices_basic()

        result = [("", "")]
        parties_with_candidates = []

        for qs in queries:
            if include_descriptions:
                qs = qs.prefetch_related("descriptions")
            for party in qs:
                parties_with_candidates.append(party)
                count_string = ""
                if party.candidate_count:
                    count_string = " ({} candidates)".format(
                        party.candidate_count
                    )

                name = "{party_name}{count_string}".format(
                    party_name=party.name, count_string=count_string
                )

                if party.date_deregistered:
                    if date.today() > party.date_deregistered:
                        if exclude_deregistered:
                            continue
                        name = "{} (Deregistered {})".format(
                            name, party.date_deregistered
                        )

                if include_descriptions and party.descriptions.exists():
                    names = [(party.ec_id, party.name)]
                    for description in party.descriptions.all():
                        joint_text = re.compile(JOINT_DESCRIPTION_REGEX, re.I)
                        party_id_str = str(party.ec_id)
                        if include_description_ids:
                            party_id_str = "{}__{}".format(
                                party_id_str, description.party.ec_id
                            )
                        if not joint_text.search(description.description):
                            names.append(
                                (party_id_str, description.description)
                            )
                    party_names = (name, names)
                else:
                    party_names = (str(party.ec_id), name)

                result.append(party_names)
        return result
