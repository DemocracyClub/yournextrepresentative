from __future__ import unicode_literals

from django.db import models
from django_extensions.db.models import TimeStampedModel


class ResultSet(TimeStampedModel):
    post_election = models.OneToOneField(
        'candidates.PostExtraElection')

    num_turnout_reported = models.IntegerField(null=True)
    num_spoilt_ballots = models.IntegerField(null=True)
    source = models.TextField(null=True)

    user = models.ForeignKey(
        'auth.User',
        related_name='result_sets',
        null=True,
    )

    ip_address = models.GenericIPAddressField(null=True)

    def __str__(self):
        return u"pk=%d user=%r post=%r" % (
            self.pk,
            self.user,
        )


class CandidateResult(TimeStampedModel):
    result_set = models.ForeignKey(
        'ResultSet',
        related_name='candidate_results',
    )

    membership = models.ForeignKey(
        'popolo.Membership',
        related_name='result',
    )

    num_ballots = models.IntegerField()
    is_winner = models.BooleanField(default=False)


    class Meta:
        ordering = ('-num_ballots',)
        unique_together = (
            ('result_set', 'membership'),
        )

    def __unicode__(self):
        return u"{} ({} votes)".format(
            self.membership.person,
            self.num_ballots
        )
