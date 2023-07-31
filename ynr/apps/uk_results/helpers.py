import csv

import requests
from candidates.models import LoggedAction
from candidates.views import get_change_metadata
from results.models import ResultEvent


class RecordBallotResultsHelper:
    """
    A helper for recording results for a ballot.

    Deals with setting elected flags as well as votes cast results
    """

    def __init__(self, ballot, user):
        """

        :type ballot: candidates.models.Ballot
        :type user: django.contrib.auth.models.User
        """
        self.ballot = ballot
        self.user = user
        self.max_winners = self.ballot.winner_count

    @property
    def existing_winners(self):
        """

        :rtype: popolo.models.Membership.objects.all
        """
        return self.ballot.membership_set.filter(elected=True)

    def _can_edit_elected(self):
        """
        Common checks for both adding and removing elected flag
        :return:
        """
        if not self.ballot.polls_closed:
            raise ValueError("Can't set winners until polls are closed")

    @property
    def can_mark_elected(self):
        """
        Checks to perform before allowing users to set the elected flag
        :return:
        """
        self._can_edit_elected()

        number_of_existing_winners = self.existing_winners.count()
        if (
            self.max_winners >= 0
            and number_of_existing_winners >= self.max_winners
        ):
            raise ValueError(
                "There were already {number} winners for {ballot_paper_id} "
                "and the maximum is {max}".format(
                    number=number_of_existing_winners,
                    ballot_paper_id=self.ballot.ballot_paper_id,
                    max=self.max_winners,
                )
            )

        return True

    @property
    def can_retract_elected(self):
        self._can_edit_elected()
        return True

    def mark_person_as_elected(self, person, source):
        candidacy = self.ballot.membership_set.get(person=person)
        if candidacy.elected:
            return
        assert self.can_mark_elected
        candidacy.elected = True
        candidacy.save()
        self.create_result_event(candidacy, source)
        self.set_not_elected()
        self.save_version(candidacy.person, source, "set-candidate-elected")

    def create_result_event(self, candidacy, source, retraction=False):
        ResultEvent.objects.create(
            election=self.ballot.election,
            winner=candidacy.person,
            old_post_id=self.ballot.post.slug,
            old_post_name=self.ballot.post.label,
            post=self.ballot.post,
            winner_party=candidacy.party,
            source=source,
            user=self.user,
            parlparse_id=candidacy.person.get_single_identifier_value(
                "theyworkforyou"
            )
            or "",
            retraction=retraction,
        )

    def save_version(self, person, source, action_type):
        change_metadata = get_change_metadata(None, source, user=self.user)
        person.record_version(change_metadata)
        person.save()

        LoggedAction.objects.create(
            user=self.user,
            action_type=action_type,
            popit_person_new_version=change_metadata["version_id"],
            person=person,
            ballot=self.ballot,
            source=change_metadata["information_source"],
        )

    def set_not_elected(self):
        """
        If the current number of winners is equal to the
        maximum number of winners, we can set everyone else as
        "not elected".

        """
        if not self.max_winners >= 0:
            return

        max_reached = self.max_winners == (self.existing_winners.count() + 1)
        if not max_reached:
            return

        losing_candidacies = self.ballot.membership_set.exclude(elected=True)
        for candidacy in losing_candidacies:
            if candidacy.elected is not False:
                candidacy.elected = False
                candidacy.save()
                candidate = candidacy.person
                change_metadata = get_change_metadata(
                    None,
                    'Setting as "not elected" by implication',
                    user=self.user,
                )
                candidate.record_version(change_metadata)
                candidate.save()

    def retract_elected(self, source="Result recorded in error, retracting"):
        assert self.can_retract_elected
        for candidacy in self.ballot.membership_set.all():
            if candidacy.elected:
                # If elected is True then a ResultEvent will have
                # been created and been included in the feed, so
                # we need to create a corresponding retraction
                # ResultEvent.
                self.create_result_event(candidacy, source, retraction=True)
                self.save_version(candidacy.person, source, "retract-winner")

            if candidacy.elected is not None:
                candidacy.elected = None
                candidacy.save()
                candidate = candidacy.person
                change_metadata = get_change_metadata(None, source, self.user)
                candidate.record_version(change_metadata)
                candidate.save()


def read_csv_from_url(url):
    """
    Takes a URL to a CSV file and iterates through the rows
    """
    response = requests.get(url, stream=True)
    response.encoding = "utf-8"
    for row in csv.DictReader(response.iter_lines(decode_unicode=True)):
        yield row
