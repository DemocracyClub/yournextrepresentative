from candidates.models import LoggedAction
from candidates.models.db import ActionType, EditType
from candidates.views.version_data import get_change_metadata
from django.conf import settings
from django.contrib.auth.models import User
from django.db import transaction
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

            if membership.elected:
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
                membership.person.save()

    def add_results(self, division=None, candidate_list=None, source=None):
        """
        # TODO DRY this and the form logic up
        """
        ballot = division.local_area

        with transaction.atomic():
            defaults = {
                "source": source,
                "num_spoilt_ballots": division.spoiled_votes,
                "turnout_percentage": division.turnout_percentage,
            }
            # Only include num_turnout_reported if it was reported in Modgov
            if division.numballotpapersissued > 0:
                defaults[
                    "num_turnout_reported"
                ] = division.numballotpapersissued
            # Same for total electorate
            if division.electorate > 0:
                defaults["total_electorate"] = division.electorate

            instance, _ = ResultSet.objects.update_or_create(
                ballot=ballot,
                defaults=defaults,
            )
            instance.user = self.user
            instance.save()

            winner_count = ballot.winner_count

            if winner_count:
                # Select the top N candidates by votes as winners
                sorted_candidates = sorted(
                    candidate_list, key=lambda c: c.votes, reverse=True
                )
                winners = {
                    f"{candidate.votes}-{candidate.ynr_membership.person.id}": candidate.ynr_membership
                    for candidate in sorted_candidates[:winner_count]
                }
                last_place_winner = sorted_candidates[winner_count - 1]
                runner_up = (
                    sorted_candidates[winner_count]
                    if len(sorted_candidates) > winner_count
                    else None
                )
            else:
                winners = {}

            tied_vote = False
            if runner_up and runner_up.votes == last_place_winner.votes:
                print(
                    "Coin flip (tied vote count) detected so skipping candidate results entry"
                )
                tied_vote = True

            if not tied_vote:
                for candidate in candidate_list:
                    membership = candidate.ynr_membership
                    rank = self.get_candidate_rank(
                        candidate.votes, candidate_list
                    )
                    instance.candidate_results.update_or_create(
                        membership=membership,
                        defaults={
                            "num_ballots": candidate.votes,
                            "rank": rank,
                        },
                    )
                    membership.elected = bool(membership in winners.values())
                    membership.save()

            versions, changed = instance.record_version()

            if changed:
                if not tied_vote:
                    self._mark_candidates_as_winner(instance)
                LoggedAction.objects.create(
                    user=instance.user,
                    action_type=ActionType.ENTERED_RESULTS_DATA,
                    source=instance.source,
                    ballot=instance.ballot,
                    edit_type=EditType.BOT.name,
                )

    def get_candidate_rank(self, num_votes, candidate_list):
        """
        Determine the rank of a candidate in the candidate list based on the number of votes.
        """
        sorted_candidates = sorted(
            candidate_list,
            reverse=True,
            key=lambda candidate: candidate.votes,
        )

        total_candidates = len(candidate_list)

        for i, candidate in enumerate(sorted_candidates, start=1):
            if num_votes == candidate.votes:
                return i
        return total_candidates + 1
