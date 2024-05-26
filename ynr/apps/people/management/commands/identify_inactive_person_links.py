import csv
from typing import List
from urllib.parse import urlparse

import requests
from django.core.management.base import BaseCommand
from people.models import Person
from popolo.models import Membership


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
        inactive_links: List[List] = []
        # facebook_url is any url with facebook or fb in the url
        memberships = Membership.objects.filter(
            ballot__election__slug="parl.2024-07-04"
        )

        people = Person.objects.all().filter(memberships__in=memberships)
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
                    resp = requests.get(identifier.value, timeout=2).status_code
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
                    inactive_links.append(
                        [
                            str(person.pk),
                            person.name,
                            identifier.value,
                            str(resp),
                        ]
                    )

        with open("inactive_links.tsv", "w") as f:
            writer = csv.writer(f)
            writer.writerow(
                ["person ID", "Person Name", "value", "status_code"]
            )
            writer.writerows(inactive_links)
