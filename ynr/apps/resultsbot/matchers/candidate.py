from parties.models import Party
from resultsbot.matchers.mappings import SavedMapping


class CandidateMatcher(object):
    def __init__(self, candidate, ballot_paper):
        self.candidate = candidate
        self.ballot_paper = ballot_paper
        self.membership_map = SavedMapping("membership_map.json")

    def match(self):
        matchers = [
            self.pick_from_map,
            self.match_party_and_name,
            self.match_manually,
            self.match_from_all_manually,
        ]
        for matcher in matchers:
            match = matcher()
            if match:
                return match
        import sys

        sys.exit()

    def get_parties(self):
        parties = [self.candidate.party]
        if self.candidate.party.ec_id == "PP53":
            parties.append(Party.objects.get(ec_id="joint-party:53-119"))
        return parties

    def get_memberships(self):
        if hasattr(self, "_memberships"):
            return self._memberships
        parties = self.get_parties()

        candidates_for_party = (
            self.ballot_paper.local_area.membership_set.filter(
                party__in=parties
            )
            .select_related("person")
            .order_by("pk")
        )
        self._memberships = candidates_for_party
        return self._memberships

    def pick_from_map(self):
        candidates_for_party = self.get_memberships()
        try:
            key = "{}--{}".format(
                self.ballot_paper.local_area.ballot_paper_id,
                self.candidate.name.encode("utf8"),
            )
        except:
            raise
        value = self.membership_map.get(key, None)
        if value:
            return self.ballot_paper.local_area.membership_set.get(pk=value)

    def match_party_and_name(self, qs=None):
        if not qs:
            candidates_for_party = self.get_memberships()
        else:
            candidates_for_party = qs
        if candidates_for_party.count() == 1:
            # Only one person it can be, init?
            return candidates_for_party.first()
        else:
            for membership in candidates_for_party:

                def _clean_name(name):
                    name = name.lower()
                    name = name.replace("  ", " ")
                    name = name.replace(",", "")
                    name = name.replace("councillor", "")
                    return name

                person_name = _clean_name(membership.person.name.lower())
                candidate_name = _clean_name(self.candidate.name.lower())

                if person_name == candidate_name:
                    return membership

                def _name_to_parts(name):
                    name = name.split(" ")
                    name = [n.strip().encode("utf8") for n in name if name]
                    return name

                split_person_name = _name_to_parts(person_name)
                split_candidate_name = _name_to_parts(candidate_name)

                # Ignore middle names
                if split_person_name[0] == split_candidate_name[0]:
                    if split_person_name[-1] == split_candidate_name[-1]:
                        return membership

                # LAST, First
                if split_person_name[-1] == split_candidate_name[0]:
                    if split_person_name[0] == split_candidate_name[-1]:
                        return membership

                print(
                    "person name {} didn't match to candidate {}".format(
                        split_person_name, split_candidate_name
                    )
                )

    def _manual_matcher(self, qs):
        print(
            "No match for '{}' in {}. Please pick from the following".format(
                self.candidate.name, self.ballot_paper.title
            )
        )
        for i, membership in enumerate(qs, start=1):
            print("\t{}\t{}".format(i, membership.person.name.encode("utf8")))
        match = input("Enter selection: ")
        if match == "s":
            return
        match = int(match)
        key = "{}--{}".format(
            self.ballot_paper.local_area.ballot_paper_id,
            self.candidate.name.encode("utf8"),
        )
        picked_membership = qs[match - 1]
        self.membership_map[key] = picked_membership.pk
        self.membership_map.save()
        return picked_membership

    def match_manually(self):
        candidates_for_party = self.get_memberships()
        if not candidates_for_party.exists():
            return
        return self._manual_matcher(candidates_for_party)

    def match_from_all_manually(self):
        qs = self.ballot_paper.local_area.membership_set.all()
        match = self.match_party_and_name(qs=qs)
        if match:
            return match
        return self._manual_matcher(qs)
