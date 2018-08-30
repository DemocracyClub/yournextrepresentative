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

    def match_name(self):
        # TODO use OtherName here
        self.remote_name = self.remote_name.lower()

        key = "{}--{}".format(self.election.slug, self.remote_name)
        if key in self.saved_matches:
            match = self.saved_matches[key]
            if match == "--deleted--":
                return "--deleted--"
            self.local_area = self.election.postextraelection_set.get(
                ballot_paper_id=match
            )
            return self.local_area

        guesses = [
            self.remote_name,
            self.remote_name.replace(" & ", " and "),
            self.remote_name.replace(" and ", " & "),
            self.remote_name.replace(" ward", "").strip(),
            self.remote_name.replace(" & ", " and ")
            .replace(" ward", "")
            .strip(),
        ]
        if self.remote_name.endswith("s"):
            guesses.append("{}'s".format(self.remote_name[:-1]))
        if self.election_specific_guess():
            guesses.append(self.election_specific_guess())

        for name in guesses:
            try:
                area = self.election.postextraelection_set.get(
                    post__label__iexact=name
                )
                self.local_area = area
                return
            except:
                continue
        # Try a regex…I know
        for name in guesses:
            try:
                name = name.replace(" ", ".")
                name = name.replace("-", ".")
                name = name + "$"
                area = self.election.postextraelection_set.get(
                    post__label__iregex=name
                )
                self.local_area = area
                return
            except:
                continue

        # If all else fails, just ask the user
        print(
            "No match for {} found. Can you manually match it?".format(
                self.remote_name
            )
        )
        possible = [
            pee
            for pee in self.election.postextraelection_set.all()
            .order_by("post__label")
            .select_related("post")
        ]
        for i, pee in enumerate(possible, start=1):
            print("\t{}\t{}".format(i, pee.post.label))
        answer = raw_input("Pick a number or 'd' if it's deleted: ")
        if answer.lower() == "d":
            self.saved_matches[key] = "--deleted--"
            self.saved_matches.save()
            return "--deleted--"
        else:
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
        return self.election.postextraelection_set.all()


class BaseCandidate(object):
    pass
