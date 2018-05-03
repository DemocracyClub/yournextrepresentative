from django.conf import settings
from django.contrib.auth.models import User
from django.db import transaction

from candidates.views.version_data import get_change_metadata
from candidates.models import LoggedAction
from results.models import ResultEvent
from uk_results.models import ResultSet


class ResultsBot(object):
    def __init__(self):
        self.user = User.objects.get(username=settings.RESULTS_BOT_USERNAME)

    def get_change_metadata_for_bot(self, source):
        """
        Wraps get_change_metadata without requiring a request object
        """
        metadata = get_change_metadata(None, source)
        metadata['username'] = self.user.username
        return metadata

    def _mark_candidates_as_winner(self, instance):
        for candidate_result in instance.candidate_results.all():
            membership = candidate_result.membership
            post_election = instance.post_election
            election = post_election.election

            source = instance.source

            change_metadata = self.get_change_metadata_for_bot(
                source
            )

            if candidate_result.is_winner:
                membership.extra.elected = True
                membership.extra.save()

                ResultEvent.objects.create(
                    election=election,
                    winner=membership.person,
                    post=post_election.postextra.base,
                    old_post_id=post_election.postextra.slug,
                    old_post_name=post_election.postextra.base.label,
                    winner_party=membership.on_behalf_of,
                    source=source,
                    user=self.user,
                )

                membership.person.extra.record_version(change_metadata)
                membership.person.save()

                LoggedAction.objects.create(
                    user=self.user,
                    action_type='set-candidate-elected',
                    popit_person_new_version=change_metadata['version_id'],
                    person=membership.person,
                    source=source,
                )
            else:
                change_metadata['information_source'] = \
                    'Setting as "not elected" by implication'
                membership.person.extra.record_version(change_metadata)
                membership.extra.elected = False
                membership.extra.save()

    def add_results(self, division=None, candidate_list=None, source=None):
        """
        # TODO DRY this and the form logic up
        """
        post_election = division.local_area

        with transaction.atomic():
            instance, _ = ResultSet.objects.update_or_create(
                post_election=post_election,
                defaults={
                    'source': source,
                    'num_spoilt_ballots': division.spoiled_votes
                }
            )
            instance.user = self.user
            instance.save()

            winner_count = post_election.winner_count

            if winner_count:
                winners = dict(sorted(
                    [("{}-{}".format(
                        c.votes,
                        c.ynr_membership.base.person.id
                        ), c.ynr_membership)
                        for c in candidate_list],
                    reverse=True,
                    key=lambda votes: int(votes[0].split('-')[0])
                )[:winner_count])
            else:
                winners = {}

            for candidate in candidate_list:
                membership_extra = candidate.ynr_membership
                instance.candidate_results.update_or_create(
                    membership=membership_extra.base,
                    defaults={
                        'is_winner':
                            bool(membership_extra in winners.values()),
                        'num_ballots': candidate.votes,
                    }
                )

            self._mark_candidates_as_winner(instance)
            versions, changed = instance.record_version()

            if changed:
                LoggedAction.objects.create(
                    user=instance.user,
                    action_type='entered-results-data',
                    source=instance.source,
                    post_election=instance.post_election,
                )
