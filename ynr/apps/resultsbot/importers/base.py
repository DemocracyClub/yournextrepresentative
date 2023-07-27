from candidates.models import Ballot
from elections.models import Election
from resultsbot.matchers.mappings import SavedMapping


class BaseDivision(object):
    """
    A representation of a division and the relationship between a remote
    source and a local Post object.
    """

    def __init__(self, election, remote_name):
        self.election = election
        self.remote_name = remote_name
        self.local_area = None
        self.saved_matches = SavedMapping("division_matches.json")

    def election_specific_guess(self):
        guesses_by_election = {
            "local.swindon.2018-05-03": {
                "Gorsehill & Pinehurst": "Gorse Hill and Pinehurst"
            }
        }
        return guesses_by_election.get(self.election.slug, {}).get(
            self.remote_name
        )

    def make_guess_list(self, name):
        name = name.strip()
        return [
            name,
            name.replace(" & ", " and "),
            name.replace(" and ", " & "),
            name.replace(" ward", "").strip(),
            name.replace(" & ", " and ").replace(" ward", "").strip(),
        ]

    def match_name(self):
        # TODO use OtherName here
        self.remote_name = self.remote_name.lower()

        key = "{}--{}".format(self.election.slug, self.remote_name)
        if key in self.saved_matches:
            match = self.saved_matches[key]
            if match == "--deleted--":
                return "--deleted--"
            self.local_area = self.election.ballot_set.get(
                ballot_paper_id=match
            )
            return self.local_area

        guesses = self.make_guess_list(self.remote_name)
        guesses += self.make_guess_list(self.remote_name.split(":")[-1])
        guesses += self.make_guess_list(self.remote_name.split("(")[0])
        guesses += self.make_guess_list(self.remote_name.split(" - ")[-1])

        if self.remote_name.endswith("s"):
            guesses.append("{}'s".format(self.remote_name[:-1]))
        if self.election_specific_guess():
            guesses.append(self.election_specific_guess())

        for name in guesses:
            try:
                area = self.election.ballot_set.exclude(
                    ballot_paper_id__in=self.matched
                ).get(post__label__iexact=name)
                self.local_area = area
                return None
            except Ballot.DoesNotExist:
                continue
        # Try a regex…I know
        for name in guesses:
            try:
                name = name.replace(" ", ".")
                name = name.replace("-", ".")
                name = name + "$"
                area = self.election.ballot_set.exclude(
                    ballot_paper_id__in=self.matched
                ).get(post__label__iregex=name)
                self.local_area = area
                return None
            except Ballot.DoesNotExist:
                continue

        # If all else fails, just ask the user
        print(
            f"""No match for found. Can you manually match it?

            "{self.remote_name}"
            """
        )
        possible = list(
            self.election.ballot_set.all()
            .exclude(ballot_paper_id__in=self.matched)
            .order_by("post__label")
            .select_related("post")
        )
        for i, ballot in enumerate(possible, start=1):
            print("\t{}\t{}".format(i, ballot.post.label))
        answer = input("Pick a number or 'd' if it's deleted: ")
        if answer.lower() == "d":
            self.saved_matches[key] = "--deleted--"
            self.saved_matches.save()
            return "--deleted--"
        answer = int(answer) - 1
        area = possible[answer]
        self.saved_matches[key] = area.ballot_paper_id
        self.saved_matches.save()
        print(area)
        self.local_area = area
        return area


class BaseImporter(object):
    def __init__(self, election_id):
        self.election_id = election_id
        self.election = Election.objects.get(slug=election_id)

    @property
    def ballot_papers(self):
        return self.election.ballot_set.all()


class BaseCandidate(object):
    pass
