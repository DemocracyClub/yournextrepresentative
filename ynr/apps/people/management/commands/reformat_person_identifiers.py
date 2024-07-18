from candidatebot.helpers import CandidateBot
from django.core.exceptions import ValidationError
from django.core.management.base import BaseCommand
from django.db import transaction
from people.helpers import (
    clean_instagram_url,
    clean_linkedin_url,
    clean_mastodon_username,
    clean_twitter_username,
    clean_wikidata_id,
)
from people.models import PersonIdentifier

# Add to this list when we have dedicated clean_* functions for an value type
supported_identifiers = {
    "instagram_url": clean_instagram_url,
    "linkedin_url": clean_linkedin_url,
    "twitter_username": clean_twitter_username,
    "mastodon_username": clean_mastodon_username,
    "wikidata_id": clean_wikidata_id,
}


class Command(BaseCommand):
    help = f"""Checks and updates links in the PersonIdentifier field. 

    Currently the fields supported are {", ".join(supported_identifiers)}.
    """

    def add_arguments(self, parser):
        parser.add_argument(
            "--update",
            help="Write changes to IDs that have been cleaned",
            action="store_true",
        )
        parser.add_argument(
            "--remove",
            help="Remove invalid IDs that can't be cleaned",
            action="store_true",
        )

    @transaction.atomic()
    def handle(self, *args, **options):
        """
        Iterate over all PersonIdentifier objects and reformat urls as needed.
        """

        if not options["update"] or not options["remove"]:
            self.stdout.write("Not modifying data, just reporting on changes.")

        person_identifiers = PersonIdentifier.objects.filter(
            value_type__in=supported_identifiers.keys()
        )
        for identifier in person_identifiers:
            initial_value = identifier.value
            try:
                cleaned_value = supported_identifiers[identifier.value_type](
                    initial_value
                )
                if initial_value != cleaned_value:
                    self.change_identifier(
                        identifier, cleaned_value, save=options["update"]
                    )

            except (ValueError, ValidationError) as exception:
                self.unclean_identifier(
                    identifier, exception, remove=options["remove"]
                )

    def change_identifier(self, identifier, cleaned_value, save=False):
        self.stdout.write(
            f"Changing person {identifier.person_id}: {identifier.value} to {cleaned_value}"
        )
        if save:
            bot = CandidateBot(identifier.person_id, update=True)
            bot.edit_field(identifier.value_type, cleaned_value)
            bot.save(source="Auto-cleaning URLs")

    def unclean_identifier(self, identifier, exception, remove=False):
        self.stdout.write(
            f"ERROR: {identifier.person_id}: {identifier.value}: {exception}"
        )
        if remove:
            bot = CandidateBot(identifier.person_id, update=True)
            bot.delete_field(identifier.value_type)
            bot.save(source="Auto removing invalid IDs")
