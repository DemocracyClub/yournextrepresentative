import json

from django.core.management.base import BaseCommand

from candidates.models.versions import get_version_for_date
from popolo.models import Membership


class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument(
            "--date",
            action="store",
            dest="date",
            help="The election date",
            required=True,
        )

    def handle(self, *args, **options):
        qs = Membership.objects.filter(
            ballot__election__election_date=options["date"],
            ballot__ballot_paper_id__startswith="parl.",
        )
        has_email = 0
        has_twitter = 0
        has_fb = 0
        has_statement = 0
        for membership in qs:
            versions = json.loads(membership.person.versions)
            version_for_date = get_version_for_date(options["date"], versions)
            if not version_for_date:
                continue
            if version_for_date["data"].get("biography"):
                has_statement += 1
            fb_fields = [
                version_for_date["data"]["facebook_personal_url"],
                version_for_date["data"]["facebook_page_url"],
            ]
            if any(fb_fields):
                has_fb += 1
            if version_for_date["data"]["email"]:
                has_email += 1
            if version_for_date["data"]["twitter_username"]:
                has_twitter += 1
        print(f"total: {qs.count()}")
        print(f"has email: {has_email}")
        print(f"has FB: {has_fb}")
        print(f"has Twitter: {has_twitter}")
        print(f"has statement: {has_statement}")
