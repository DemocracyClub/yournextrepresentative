from django.core.management.base import BaseCommand
from django.db import IntegrityError
from candidatebot.helpers import CandidateBot
from people.models import Person
from uk_results.helpers import read_csv_from_url


class Command(BaseCommand):
    help = "Import candidates twitter usernames from a google sheet"

    def add_arguments(self, parser):
        parser.add_argument("--url", action="store", required=False)
        parser.add_argument(
            "--update",
            action="store_true",
            default=False,
            required=False,
            help="When used will update existing twitter usernames",
        )

    def handle(self, *args, **options):

        url = "https://docs.google.com/spreadsheets/d/e/2PACX-1vRZgJoqxpSSTs5hD5X-x4jt9i88Iv6amoJUwRokNS2G4EUkA368OQS7HTwJiJxrKhQKvKBfjIkXbNHz/pub?gid=0&single=true&output=csv"
        if options["url"]:
            url = options["url"]

        for row in read_csv_from_url(url=url):
            person_id = row.get("person_id")
            twitter_username = row.get("twitter_username")
            if not all([person_id, twitter_username]):
                continue

            try:
                bot = CandidateBot(person_id=person_id)
            except Person.DoesNotExist:
                self.stdout.write(f"Couldn't find Person with ID {person_id}")
            try:
                bot.add_twitter_username(
                    username=twitter_username, update=options["update"]
                )
                bot.save(source=url)
                self.stdout.write(
                    f"Updated Person {person_id} twitter username to {twitter_username}"
                )
            except IntegrityError:
                self.stdout.write(
                    f"Twitter username already exists for Person {person_id}, skipping"
                )
                continue
