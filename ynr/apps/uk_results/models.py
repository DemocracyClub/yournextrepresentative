from django.contrib.postgres.fields import JSONField
from django.db import models
from django_extensions.db.models import TimeStampedModel


class ResultSet(TimeStampedModel):
    post_election = models.OneToOneField("candidates.PostExtraElection")

    num_turnout_reported = models.IntegerField(
        null=True, verbose_name="Reported Turnout"
    )
    num_spoilt_ballots = models.IntegerField(
        null=True, verbose_name="Spoilt Ballots"
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
        return "Result for {}".format(self.post_election.ballot_paper_id)

    def as_dict(self):
        """
        A representation of the model and related CandidateResult models
        as JSON.

        Used for storing versions.

        # TODO use API serializer for this?
        """
        data = {
            "created": self.created.isoformat(),
            "ballot_paper_id": self.post_election.ballot_paper_id,
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

    def record_version(self, force=False, save=True):
        existing = self.versions
        this_version = self.as_dict()
        changed = False
        if existing:
            latest = existing[0]
            if force or latest != this_version:
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

    num_ballots = models.IntegerField()
    is_winner = models.BooleanField(default=False)

    class Meta:
        ordering = ("-num_ballots",)
        unique_together = (("result_set", "membership"),)

    def __unicode__(self):
        return "{} ({} votes)".format(self.membership.person, self.num_ballots)
