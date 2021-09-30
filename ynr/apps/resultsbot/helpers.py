from django.conf import settings
from django.contrib.auth.models import User
from django.db import transaction

from candidates.models import LoggedAction
from candidates.models.db import EditType, ActionType
from candidates.views.version_data import get_change_metadata
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
        metadata["username"] = self.user.username
        return metadata

    def _mark_candidates_as_winner(self, instance):
        for candidate_result in instance.candidate_results.all():
            membership = candidate_result.membership
            ballot = instance.ballot
            election = ballot.election

            source = instance.source

            change_metadata = self.get_change_metadata_for_bot(source)

            if candidate_result.is_winner:
                membership.elected = True
                membership.save()

                ResultEvent.objects.create(
                    election=election,
                    winner=membership.person,
                    post=ballot.post,
                    old_post_id=ballot.post.slug,
                    old_post_name=ballot.post.label,
                    winner_party=membership.party,
                    source=source,
                    user=self.user,
                )

                membership.person.record_version(change_metadata)
                membership.person.save()

                LoggedAction.objects.create(
                    user=self.user,
                    action_type=ActionType.SET_CANDIDATE_ELECTED,
                    popit_person_new_version=change_metadata["version_id"],
                    person=membership.person,
                    source=source,
                    edit_type=EditType.BOT.name,
                )
            else:
                change_metadata[
                    "information_source"
                ] = 'Setting as "not elected" by implication'
                membership.person.record_version(change_metadata)
                membership.elected = False
                membership.save()

    def add_results(self, division=None, candidate_list=None, source=None):
        """
        # TODO DRY this and the form logic up
        """
        ballot = division.local_area

        with transaction.atomic():
            instance, _ = ResultSet.objects.update_or_create(
                ballot=ballot,
                defaults={
                    "source": source,
                    "num_spoilt_ballots": division.spoiled_votes,
                },
            )
            instance.user = self.user
            instance.save()

            winner_count = ballot.winner_count

            if winner_count:
                winners = dict(
                    sorted(
                        [
                            (
                                "{}-{}".format(
                                    c.votes, c.ynr_membership.person.id
                                ),
                                c.ynr_membership,
                            )
                            for c in candidate_list
                        ],
                        reverse=True,
                        key=lambda votes: int(votes[0].split("-")[0]),
                    )[:winner_count]
                )
            else:
                winners = {}

            for candidate in candidate_list:
                membership = candidate.ynr_membership
                instance.candidate_results.update_or_create(
                    membership=membership,
                    defaults={
                        "is_winner": bool(membership in winners.values()),
                        "num_ballots": candidate.votes,
                    },
                )

            versions, changed = instance.record_version()

            if changed:
                self._mark_candidates_as_winner(instance)
                LoggedAction.objects.create(
                    user=instance.user,
                    action_type=ActionType.ENTERED_RESULTS_DATA,
                    source=instance.source,
                    ballot=instance.ballot,
                    edit_type=EditType.BOT.name,
                )
