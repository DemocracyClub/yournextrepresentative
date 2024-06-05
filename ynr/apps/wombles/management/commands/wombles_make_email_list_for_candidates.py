import csv
import hashlib
import json
import sys

from django.contrib.auth.models import User
from django.core.management.base import BaseCommand
from popolo.models import Membership
from sesame.utils import get_token


class NoEmailError(ValueError):
    ...


def make_fake_username(email):
    hash_object = hashlib.sha256(email.encode())
    # Convert the hash object to a hexadecimal string
    hashed_email = hash_object.hexdigest()
    # Optionally, you can shorten the hash for the username (e.g., first 10 characters)
    return f"@@{hashed_email[:10]}"


class Command(BaseCommand):
    def add_arguments(self, parser):
        super().add_arguments(parser)

        parser.add_argument(
            "--election-date", help="Date of the election", required=True
        )
        parser.add_argument(
            "--election-type",
            help="Election Type",
        )

    def handle(self, *args, **options):
        qs = Membership.objects.filter(
            ballot__election__election_date=options["election_date"]
        )

        if election_type := options.get("election_type"):
            qs = qs.filter(ballot__election__slug__startswith=election_type)

        out_csv = csv.writer(sys.stdout)
        out_csv.writerow(["email", "name", "attributes"])

        attrs = {"onboarded": 1}

        for membership in qs:
            try:
                user = self.get_user(membership.person)
            except NoEmailError:
                continue

            auth_link = self.make_auth_link(membership.person, user)
            user_attrs = attrs.copy()
            user_attrs["login_url"] = auth_link
            out_csv.writerow(
                [user.email, membership.person.name, json.dumps(user_attrs)]
            )

    def get_user(self, person):
        email = person.get_email
        if not email:
            raise NoEmailError()

        try:
            return User.objects.get(email=email)
        except User.DoesNotExist:
            user = User.objects.create(
                username=make_fake_username(email), email=email
            )
            user.set_unusable_password()
            user.save()
            return user

    def make_auth_link(self, person, user):
        base_url = "https://candidates.democracyclub.org.uk"
        next_url = person.get_absolute_url()

        scope_name = "candidate_email"
        token = get_token(user, scope=scope_name)

        return f"{base_url}/accounts/authenticate/?login_token={token}&scope={scope_name}&next={next_url}"
