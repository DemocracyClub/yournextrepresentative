import datetime
import re

import requests
from django.core.management.base import BaseCommand

from people.models import EditLimitationStatuses, Person


class Command(BaseCommand):
    def handle(self, **options):
        req = requests.get(
            "https://github.com/mysociety/parlparse/raw/master/members/ministers-2010.json"
        )

        today = str(datetime.date.today())

        for minister in req.json()["memberships"]:
            if not re.search(
                r"^(Minister|The Secretary of State|Deputy Prime Minister|The Prime Minister)",
                minister.get("role", ""),
            ):
                continue

            if not (
                today >= minister["start_date"]
                and today <= minister.get("end_date", "9999-12-31")
            ):
                continue

            try:
                person = Person.objects.get(
                    tmp_person_identifiers__internal_identifier=minister[
                        "person_id"
                    ]
                )
            except Person.DoesNotExist:
                # There will be lords in the government that never got elected…
                continue

            person.edit_limitations = EditLimitationStatuses.NEEDS_REVIEW.name
            person.save()
