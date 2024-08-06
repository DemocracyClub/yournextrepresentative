from django.core.management import call_command
from django.core.management.base import BaseCommand
from people.models import PersonIdentifier


class Command(BaseCommand):
    def handle(self, *args, **options):
        """
        Iterate over all PersonIdentifier objects and reformat urls as needed.
        """

        person_identifiers = PersonIdentifier.objects.all().filter(
            value_type="instagram_url"
        )
        for identifier in person_identifiers:
            if identifier.value.startswith("https"):
                self.stdout.write(
                    f"URL for {identifier.person.name} is already in the correct format."
                )
                pass

            if identifier.value.startswith("@"):
                identifier.value = (
                    f"https://www.instagram.com/{identifier.value[1:]}"
                )
                identifier.save()
                self.stdout.write(
                    f"Reformatted LinkedxIn URL for {identifier.person.name} to {identifier.value}"
                )

        call_command("identify_inactive_person_links")
