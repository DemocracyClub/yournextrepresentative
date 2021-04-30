from django.contrib.postgres.fields import JSONField
from django.db import models
from django_extensions.db.models import TimeStampedModel


class ResultSet(TimeStampedModel):
    ballot = models.OneToOneField("candidates.Ballot", on_delete=models.CASCADE)

    num_turnout_reported = models.PositiveIntegerField(
        null=True, verbose_name="Reported Turnout"
    )
    num_spoilt_ballots = models.PositiveIntegerField(
        null=True, verbose_name="Spoilt Ballots"
    )
    total_electorate = models.PositiveIntegerField(null=True, blank=True)
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
            "source": self.source,
            "user": getattr(self.user, "username", None),
            "candidate_results": [],
        }

        for result in self.candidate_results.all():
            data["candidate_results"].append(
                {
                    "num_ballots": result.num_ballots,
                    "is_winner": result.is_winner,
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
