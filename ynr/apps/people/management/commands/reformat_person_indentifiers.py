from urllib.parse import urlparse

from django.core.management import call_command
from django.core.management.base import BaseCommand
from people.models import Person


class Command(BaseCommand):
    def handle(self, *args, **options):
        """
        Iterate over all PersonIdentifier objects and reformat the LinkedIn urls as needed.
        """

        people = Person.objects.all()
        for person in people:
            person_identifiers = person.get_all_identifiers
            linkedin_person_identifiers = [
                identifier
                for identifier in person_identifiers
                if identifier.value_type == "linkedin_url"
            ]
            # if the parsed_url netloc is uk.linkedin.com,
            # then this is a redirect and we need to reformat it to www.linkedin.com
            for identifier in linkedin_person_identifiers:
                parsed_url = urlparse(identifier.value)

            if parsed_url.netloc == "uk.linkedin.com":
                # remove the uk. from the netloc
                identifier.value = identifier.value.replace("uk.", "www.")
                identifier.save()
                self.stdout.write(
                    f"Reformatted LinkedIn URL for {person.name} to {identifier.value}"
                )
            else:
                self.stdout.write(
                    f"LinkedIn URL for {person.name} is already in the correct format."
                )
                pass

        call_command("identify_inactive_person_links")
