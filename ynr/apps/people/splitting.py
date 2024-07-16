import json
import sys

from people.models import Person
from popolo.models import Membership


class PersonCandidacySplitter:
    split_on_candidacy: Membership

    def __init__(self, person_id, stdout=sys.stdout):
        self.person_id = person_id
        self.person = Person.objects.get(pk=person_id)
        self.stdout = stdout
        self.split_on_candidacy = None

    @property
    def possible_candidacies(self):
        return self.person.memberships.all()

    def candidacy_picker(self):
        """
        :rtype: popolo.models.Membership
        """
        for i, candidacy in enumerate(self.possible_candidacies, start=1):
            self.stdout.write(
                "{}\t{}".format(i, candidacy.ballot.ballot_paper_id)
            )
        selected = input("Enter the FIRST candidacy for the NEW person: ")
        self.split_on_candidacy = self.possible_candidacies[int(selected) - 1]
        return self.split_on_candidacy

    def find_version_to_revert_to(self):
        """
        Get the latest version of the initial person. e.g, the one
        just before the incorrect candidacy was added
        """
        if not self.split_on_candidacy:
            raise ValueError("No candidacy to split on")

        election = self.split_on_candidacy.ballot.election
        post = self.split_on_candidacy.ballot.post
        for version in json.loads(self.person.versions):
            candidacies = version["data"]["standing_in"]
            if election.slug in candidacies:
                if (
                    version["data"]["standing_in"][election.slug]["post_id"]
                    == post.slug
                ):
                    continue
            print(version)
            return
