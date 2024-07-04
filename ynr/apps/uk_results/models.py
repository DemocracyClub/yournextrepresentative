from data_exports.models import MaterializedMemberships
from django.contrib.auth.models import User
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models, transaction
from django.db.models import JSONField, OuterRef, Subquery
from django_extensions.db.models import TimeStampedModel
from popolo.models import Membership


class ResultSet(TimeStampedModel):
    ballot = models.OneToOneField("candidates.Ballot", on_delete=models.CASCADE)

    num_turnout_reported = models.PositiveIntegerField(
        null=True, verbose_name="Reported Turnout"
    )
    turnout_percentage = models.IntegerField(
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        blank=True,
        null=True,
    )
    num_spoilt_ballots = models.PositiveIntegerField(
        null=True, verbose_name="Spoilt Ballots"
    )
    total_electorate = models.PositiveIntegerField(
        verbose_name="Total Electorate", null=True, blank=True
    )
    source = models.TextField(null=True)

    user = models.ForeignKey(
        "auth.User",
        related_name="result_sets",
        null=True,
        on_delete=models.CASCADE,
    )
    versions = JSONField(default=list)

    ip_address = models.GenericIPAddressField(null=True)

    def __str__(self):
        return "Result for {}".format(self.ballot.ballot_paper_id)

    @property
    def rank(self):
        self.ballot.result_sets.order_by("-num_turnout_reported").index(self)

    def calculate_turnout_percentage(self):
        """
        Return turnout as a percentage, rounded to two decimal places
        """
        if not all([self.num_turnout_reported, self.total_electorate]):
            return

        percentage = (self.num_turnout_reported / self.total_electorate) * 100
        self.turnout_percentage = int(min(round(percentage, 2), 100))

    def as_dict(self):
        """
        A representation of the model and related CandidateResult models
        as JSON.

        Used for storing versions.

        # TODO use API serializer for this?
        """
        data = {
            "created": self.modified.isoformat(),
            "ballot_paper_id": self.ballot.ballot_paper_id,
            "turnout": self.num_turnout_reported,
            "spoilt_ballots": self.num_spoilt_ballots,
            "total_electorate": self.total_electorate,
            "source": self.source,
            "user": getattr(self.user, "username", None),
            "candidate_results": [],
        }

        for result in self.candidate_results.all():
            data["candidate_results"].append(
                {
                    "num_ballots": result.num_ballots,
                    "elected": result.membership.elected,
                    "person_id": result.membership.person_id,
                    "person_name": result.membership.person.name,
                }
            )
        return data

    def versions_equal(self, v1, v2):
        """
        Compare v1 and v2, ignoring the created key
        """
        ignore_keys = ["created"]
        comp1 = {k: v for k, v in v1.items() if k not in ignore_keys}
        comp2 = {k: v for k, v in v2.items() if k not in ignore_keys}
        return comp1 == comp2

    def record_version(self, force=False, save=True):
        existing = self.versions
        this_version = self.as_dict()
        changed = False
        if existing:
            latest = existing[0]
            if force or not self.versions_equal(latest, this_version):
                changed = True
                existing.insert(0, this_version)
        else:
            changed = True
            existing.insert(0, this_version)

        self.versions = existing
        if save:
            self.save()
        return (existing, changed)

    def save(self, **kwargs):
        self.calculate_turnout_percentage()
        return super().save(**kwargs)


class CandidateResult(TimeStampedModel):
    result_set = models.ForeignKey(
        "ResultSet", related_name="candidate_results", on_delete=models.CASCADE
    )

    membership = models.OneToOneField(
        "popolo.Membership", related_name="result", on_delete=models.CASCADE
    )

    num_ballots = models.PositiveIntegerField()
    tied_vote_winner = models.BooleanField(
        default=False,
        help_text="Did this person win after receiving same votes as another candidate, via coin toss, lots etc",
    )
    rank = models.PositiveIntegerField(null=True, verbose_name="Results Rank")

    class Meta:
        ordering = ("-num_ballots",)
        unique_together = (("result_set", "membership"),)

    def __unicode__(self):
        return "{} ({} votes)".format(self.membership.person, self.num_ballots)


# Useful when debugging
ALWAYS_REFRESH = False


class SuggestedWinner(TimeStampedModel):
    """
    Model that tracks when someone has marked a person as a winner
    by directly pressing a button, rather than entering votes cast.

    If the last `N_SUGGESTIONS_NEEDED` agree, then we mark the winner.

    """

    N_SUGGESTIONS_NEEDED = 2

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    membership = models.ForeignKey(
        Membership, related_name="suggested_winners", on_delete=models.CASCADE
    )
    is_elected = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.membership.party.ec_id}: {self.is_elected} ({self.user})"

    @classmethod
    def record_suggestion(
        cls, user: User, membership: Membership, is_elected: bool = True
    ):
        ballot = membership.ballot
        if ballot.winner_count > 1:
            raise ValueError(
                "Can't use mark winner system for multi-seat posts"
            )
        with transaction.atomic():
            # Create or update the vote
            suggestion, created = cls.objects.update_or_create(
                user=user,
                membership=membership,
                defaults={"is_elected": is_elected},
            )

            # If a different winner is already set on the ballot,
            # we shouldn't have allowed a user to make a suggestion.
            # We're here now though, so we still record the above, but
            # do nothing else
            other_winners = ballot.membership_set.filter(elected=True).exclude(
                pk=membership.pk
            )
            if other_winners.exists():
                return suggestion

            # Retrieve the last two votes for the membership
            subquery = (
                cls.objects.filter(user=OuterRef("user"), membership=membership)
                .order_by("-id")
                .values("id")[:1]
            )

            latest_votes = (
                cls.objects.filter(membership=membership)
                .annotate(latest_id=Subquery(subquery))
                .filter(id=Subquery(subquery))[:2]
            )

            elected_count = sum(v.is_elected for v in latest_votes)
            if elected_count == cls.N_SUGGESTIONS_NEEDED:
                membership.elected = True
                membership.save()
                if ALWAYS_REFRESH:
                    MaterializedMemberships.refresh_view()
                return suggestion
            if not is_elected:
                membership.elected = False
                membership.save()
                if ALWAYS_REFRESH:
                    MaterializedMemberships.refresh_view()
            return suggestion
