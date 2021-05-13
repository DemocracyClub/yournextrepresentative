from django.db.models import JSONField
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django_extensions.db.models import TimeStampedModel


class ResultSet(TimeStampedModel):
    ballot = models.OneToOneField("candidates.Ballot", on_delete=models.CASCADE)

    num_turnout_reported = models.PositiveIntegerField(
        null=True, verbose_name="Reported Turnout"
    )
    turnout_percentage = models.FloatField(
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

    def calculate_turnout_percentage(self):
        """
        Return turnout as a percentage, rounded to two decimal places
        """
        if not all([self.num_turnout_reported, self.total_electorate]):
            return None

        percentage = (self.num_turnout_reported / self.total_electorate) * 100
        self.turnout_percentage = min(round(percentage, 2), 100)

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
    is_winner = models.BooleanField(default=False)
    tied_vote_winner = models.BooleanField(
        default=False,
        help_text="Did this person win after receiving same votes as another candidate, via coin toss, lots etc",
    )

    class Meta:
        ordering = ("-num_ballots",)
        unique_together = (("result_set", "membership"),)

    def __unicode__(self):
        return "{} ({} votes)".format(self.membership.person, self.num_ballots)
