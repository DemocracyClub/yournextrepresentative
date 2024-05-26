import requests
from candidatebot.helpers import CandidateBot
from django.core.management import BaseCommand
from elections.models import Election


class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument(
            "--election-date", help="Date of the election", required=True
        )
        parser.add_argument(
            "--api-key", help="Labour Party API key", required=True
        )

    def handle(self, **options):
        API_URL = "https://vote.labour.org.uk/api/v1/candidates"
        API_PARAMS = {"token": options["api_key"]}

        self.election = Election.objects.get(
            slug__startswith="parl", election_date=options["election_date"]
        )

        req = requests.get(API_URL, params=API_PARAMS)
        req.raise_for_status()
        for person in req.json()["data"]:
            self.import_person(person)

    def import_person(self, person_json):
        post = self.election.posts.get(
            identifier__contains=person_json["constituency"]["ons_code"]
        )
        ballot = self.election.ballot_set.get(post=post)

        try:
            membership = ballot.membership_set.filter(
                party__ec_id__in=["PP53", "joint-party:53-119"]
            ).get()
        except ballot.membership_set.model.DoesNotExist:
            self.stdout.write(
                f"Labour has a candidate for {ballot.ballot_paper_id} that we don't have: {person_json['full_name']}"
            )
            return
        except ballot.membership_set.model.MultipleObjectsReturned:
            self.stdout.write(
                f"More than one Labour membership for {ballot.ballot_paper_id}"
            )
            return

        person = membership.person
        bot = CandidateBot(person.pk, ignore_errors=True, update=True)
        bot.add_twitter_username(person_json["twitter_username"])
        bot.add_email(person_json["email"])
        bot.edit_field("instagram_url", person_json["instagram_username"])
        bot.edit_field("youtube_profile", person_json["youtube_url"])
        bot.edit_field("homepage_url", person_json["website"])
        bot.edit_field("facebook_page_url", person_json["facebook_url"])
        bot.edit_field("biography", person_json["statement"])
        bot.save(source="Labour API")
