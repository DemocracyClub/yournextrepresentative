from popolo.models import Identifier, OtherName, Organization
from parties.models import Party, PartyDescription

from resultsbot.matchers.mappings import SavedMapping


class PartyMatacher(object):
    """
    Takes a string and tries to return an Organisation that matches the party
    """

    def __init__(self, party_name):
        self.party_name = party_name
        self.known_names_to_ids = SavedMapping("party_names.json")

    def clean_party_names(self):
        name_options = []
        self.party_name = self.party_name.lower()
        name_options.append(self.party_name.replace(" party", ""))
        name_options.append(self.party_name.replace("the ", ""))
        name_options.append(self.party_name.replace(" tory ", "conservative"))
        name_options.append(
            self.party_name.replace(" libdem ", "liberal democrats")
        )
        for name in name_options[:]:
            name_options.append(self.clean_party_name(name))
        return name_options

    def clean_party_name(self, name):
        # TODO differernt registers / countries
        return self.known_names_to_ids.get(name, name)

    def match_party_id(self, cleaned_name):
        try:
            return Party.objects.get(ec_id=cleaned_name)
        except:
            return None

    def match_party_name(self, cleaned_name):
        try:
            Party.objects.get(name__iexact=cleaned_name)
        except:
            return None

    def match_party_description(self, cleaned_name):
        try:
            PartyDescription.objects.get(name__iexact=cleaned_name)
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
        raise ValueError(
            "No match for {} (cleaned to {})".format(
                self.party_name, repr(cleaned_name)
            )
        )
