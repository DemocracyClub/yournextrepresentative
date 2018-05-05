# -*- coding: utf-8 -*-
import os
import json

from elections.models import Election
from candidates.models import OrganizationExtra
from popolo.models import OtherName, Identifier
import resultsbot


class BaseDivision(object):
    """
    A representation of a division and the relationship between a remote
    source and a local Post object.
    """
    def __init__(self, election, remote_name):
        self.election = election
        self.remote_name = remote_name
        self.local_area = None
        self.saved_matches = SavedMapping('division_matches.json')

    def election_specific_guess(self):
        guesses_by_election = {
            'local.swindon.2018-05-03': {
                'Gorsehill & Pinehurst': 'Gorse Hill and Pinehurst'
            }
        }
        return guesses_by_election.get(
            self.election.slug, {}).get(self.remote_name)

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
            self.remote_name.replace(' & ', ' and '),
            self.remote_name.replace(' and ', ' & '),
            self.remote_name.replace(' ward', '').strip(),
            self.remote_name.replace(
                ' & ', ' and ').replace(' ward', '').strip(),
        ]
        if self.remote_name.endswith('s'):
            guesses.append(
                "{}'s".format(self.remote_name[:-1])
            )
        if self.election_specific_guess():
            guesses.append(self.election_specific_guess())

        for name in guesses:
            try:
                area = self.election.postextraelection_set.get(
                    postextra__base__label__iexact=name)
                self.local_area = area
                return
            except:
                continue
        # Try a regex…I know
        for name in guesses:
            try:
                name = name.replace(' ', '.')
                name = name.replace('-', '.')
                name = name + "$"
                area = self.election.postextraelection_set.get(
                    postextra__base__label__iregex=name)
                self.local_area = area
                return
            except:
                continue

        # If all else fails, just ask the user
        print("No match for {} found. Can you manually match it?".format(
            self.remote_name
        ))
        possible = [
            pee
            for pee in self.election.postextraelection_set.all().order_by(
                'postextra__base__label'
            ).select_related('postextra__base')
        ]
        for i, pee in enumerate(possible, start=1):
            print ("\t{}\t{}".format(i, pee.postextra.base.label))
        answer = raw_input("Pick a number or 'd' if it's deleted: ")
        if answer.lower() == 'd':
            self.saved_matches[key] = "--deleted--"
            self.saved_matches.save()
            return "--deleted--"
        else:
            answer = int(answer)-1
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

class SavedMapping(dict):
    def __init__(self, file_name):
        self.file_name = file_name
        self.path = os.path.join(
            os.path.dirname(resultsbot.__file__),
            self.file_name
        )
        self.load()

    def load(self):
        try:
            self.update(json.loads(open(self.path).read()))
        except IOError:
            with open(self.path,'w') as f:
                f.write('{}')

    def save(self):
        with open(self.path, 'w') as f:
            f.write(json.dumps(self, indent=4, sort_keys=True))

    def picker(self, name):
        print("No match for '{}' found. Can you enter a manual match?".format(
            name
        ))
        print("This match will be saved for future in {}".format(self.path))
        match = raw_input("New name or ID: ")
        self.update({name: match})
        self.save()
        return match


class PartyMatacher(object):
    """
    Takes a string and tries to return an Organisation that matches the party
    """
    def __init__(self, party_name):
        self.party_name = party_name
        self.known_names_to_ids = SavedMapping('party_names.json')

    def clean_party_names(self):
        name_options = []
        self.party_name = self.party_name.lower()
        name_options.append(self.party_name.replace(' party', ''))
        name_options.append(self.party_name.replace('the ', ''))
        name_options.append(self.party_name.replace(' tory ', 'conservative'))
        name_options.append(self.party_name.replace(' libdem ', 'liberal democrats'))
        for name in name_options[:]:
            name_options.append(self.clean_party_name(name))
        return name_options

    def clean_party_name(self, name):
        # TODO differernt registers / countries
        return self.known_names_to_ids.get(
            name, name)

    def match_party_id(self, cleaned_name):
        try:
            return Identifier.objects.get(
                identifier=cleaned_name).content_object
        except:
            return None

    def match_party_name(self, cleaned_name):
        try:
            OrganizationExtra.objects.get(
                base__name__iexact=cleaned_name)
        except:
            return None

    def match_party_description(self, cleaned_name):
        try:
            OtherName.objects.get(
                name__iexact=cleaned_name).content_object
        except Exception as e:
            return None

    def match(self, picker=True):
        matchers = [
            self.match_party_id,
            self.match_party_name,
            self.match_party_description,
        ]

        cleaned_names = self.clean_party_names()
        for cleaned_name in cleaned_names:
            for matcher in matchers:
                match = matcher(cleaned_name)
                if match:
                    return match
        if picker:
            self.known_names_to_ids.picker(self.party_name)
            return self.match(picker=False)
        raise ValueError("No match for {} (cleaned to {})".format(
            self.party_name, repr(cleaned_name)
        ))


class CandidateMatcher(object):
    def __init__(self, candidate, ballot_paper):
        self.candidate = candidate
        self.ballot_paper = ballot_paper
        self.membership_map = SavedMapping('membership_map.json')

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
        parties =  [self.candidate.party]
        if self.candidate.party.identifiers.filter(identifier="PP53"):
            parties.append(
                Identifier.objects.get(
                    identifier="joint-party:53-119").content_object
            )
        return parties

    def get_memberships(self):
        if hasattr(self, '_memberships'):
            return self._memberships
        parties = self.get_parties()

        candidates_for_party = \
            self.ballot_paper.local_area.membershipextra_set.filter(
                base__on_behalf_of__in=parties
            ).select_related('base__person').order_by('pk')
        self._memberships = candidates_for_party
        return self._memberships

    def pick_from_map(self):
        candidates_for_party = self.get_memberships()
        try:
            key = "{}--{}".format(
                self.ballot_paper.local_area.ballot_paper_id,
                self.candidate.name.encode('utf8'),
            )
        except:
            import ipdb; ipdb.set_trace()
        value = self.membership_map.get(key, None)
        if value:
            return self.ballot_paper.local_area.membershipextra_set.get(
                pk=value)


    def match_party_and_name(self):
        candidates_for_party = self.get_memberships()
        if candidates_for_party.count() == 1:
            # Only one person it can be, init?
            return candidates_for_party.first()
        else:
            for membership in candidates_for_party:

                def _clean_name(name):
                    name =name.lower()
                    name =name.replace('  ', ' ')
                    name =name.replace(',', '')
                    name =name.replace('councillor', '')
                    return name

                person_name = _clean_name(membership.base.person.name.lower())
                candidate_name = _clean_name(self.candidate.name.lower())

                if  person_name == candidate_name:
                    return membership

                def _name_to_parts(name):
                    name = name.split(' ')
                    name = [n.strip().encode('utf8') for n in name]
                    return name

                split_person_name = _name_to_parts(person_name)
                split_candidate_name = _name_to_parts(candidate_name)

                # Ignore middle names
                if split_person_name[0] == split_candidate_name[0]:
                    if split_person_name[-1] == split_candidate_name[-1]:
                        return membersip

                # LAST, First
                if split_person_name[-1] == split_candidate_name[0]:
                    if split_person_name[0] == split_candidate_name[-1]:
                        return membership

                print("person name {} didn't match to candidate {}".format(
                    split_person_name,
                    split_candidate_name
                ))

    def _manual_matcher(self, qs):
        print("No match for '{}' in {}. Please pick from the following".format(
            self.candidate.name,
            self.ballot_paper.title
        ))
        for i, membership in enumerate(qs, start=1):
            print("\t{}\t{}".format(i, membership.base.person.name.encode('utf8')))
        match = raw_input("Enter selection: ")
        if match == "s":
            return
        match = int(match)
        key = "{}--{}".format(
            self.ballot_paper.local_area.ballot_paper_id,
            self.candidate.name.encode('utf8'),
        )
        picked_membership = qs[match-1]
        self.membership_map[key] = picked_membership.pk
        self.membership_map.save()
        return picked_membership


    def match_manually(self):
        candidates_for_party = self.get_memberships()
        if not candidates_for_party.exists():
            return
        return self._manual_matcher(candidates_for_party)

    def match_from_all_manually(self):
        return self._manual_matcher(
            self.ballot_paper.local_area.membershipextra_set.all()
        )
