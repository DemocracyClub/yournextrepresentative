from urllib.parse import urlparse

import requests
from django.core.management.base import BaseCommand
from people.models import Person


def get_domain(url):
    parsed_url = urlparse(url)
    return parsed_url.netloc


def is_facebook_url(url):
    domain = get_domain(url)
    return "facebook.com" in domain or "fb.com" in domain


class Command(BaseCommand):
    """
    Test and remove inactive or dead links from Person objects.
    """

    def handle(self, *args, **options):
        """
        Iterate over all Person objects and check if the
        person identifier urls return a 200 status code.
        """
        inactive_links = []
        # facebook_url is any url with facebook or fb in the url

        people = Person.objects.all()
        for person in people:
            person_identifiers = person.get_all_identifiers
            person_identifiers = [
                identifier
                for identifier in person_identifiers
                if identifier.value.startswith("http")
            ]

            if not person_identifiers:
                continue
            for identifier in person_identifiers:
                resp = None
                try:
                    resp = requests.head(identifier.value).status_code
                except requests.exceptions.RequestException as e:
                    self.stdout.write(
                        f"Request exception: {e} for {person.name}"
                    )
                    pass
                if resp in [
                    404,
                    500,
                    502,
                    503,
                    504,
                ] and not is_facebook_url(identifier.value):
                    self.stdout.write(
                        f"Status code: {resp} for {person.name} {identifier.value}"
                    )
                    inactive_links.append(identifier)

                    with open("inactive_links.tsv", "w") as f:
                        f.write("person\tidentifier\tvalue\tstatus_code\n")
                        for link in inactive_links:
                            f.write(
                                f"{person.name}\t{identifier}\t{identifier.value}\t{resp}\n"
                            )
                            f.close()
