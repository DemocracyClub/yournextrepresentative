import json
import re
from datetime import datetime
from pathlib import Path

from django.core.management.base import BaseCommand

from parties.models import Party, PartySpending, PartyAccounts, PartyDonations


class Command(BaseCommand):
    CACHE = {"parties": {}}

    def add_arguments(self, parser):
        parser.add_argument(
            "--data-path",
            action="store",
            help="Path to the `data` dir of the scraper",
            required=True,
        )
        parser.add_argument(
            "--type",
            action="store",
            help="Currently only 'spending' supported",
            default="Spending",
        )

    def populate_parties_cache(self):
        for party in Party.objects.all():
            self.CACHE["parties"][party.ec_id] = party

    def add_spending(self, data: dict):
        party_id = f"{data.get('RegulatedEntityTypeShortcode')}{data.get('RegulatedEntityId')}"
        party: Party = self.CACHE["parties"].get(party_id)
        if not party:
            return
        print(party, data.get("RegulatedEntityName"))
        spending, updated = PartySpending.objects.update_or_create(
            party=party,
            ec_id=data["ECRef"],
            defaults={
                "raw_data": data,
                "published": self.clean_date(data["PublishedDate"]),
            },
        )
        return spending

    def add_accounts(self, data: dict):
        party_id = f"{data.get('RegulatedEntityTypeShortcode')}{data.get('RegulatedEntityId')}"
        party: Party = self.CACHE["parties"].get(party_id)
        if not party:
            return
        accounts, updated = PartyAccounts.objects.update_or_create(
            party=party,
            ec_id=data["ECRef"],
            defaults={
                "raw_data": data,
                "published": self.clean_date(data["PublishedDate"]),
            },
        )
        return accounts

    def add_donations(self, data: dict):
        party_id = f"{data.get('RegulatedEntityTypeShortcode')}{data.get('RegulatedEntityId')}"
        party: Party = self.CACHE["parties"].get(party_id)
        if not party:
            return
        accounts, updated = PartyDonations.objects.update_or_create(
            party=party,
            ec_id=data["ECRef"],
            defaults={
                "raw_data": data,
                "published": self.clean_date(data["PublishedDate"]),
            },
        )
        return accounts

    def clean_date(self, date):
        try:
            timestamp = re.match(r"/Date\(([\-]?\d+)\)/", date).group(1)
            dt = datetime.fromtimestamp(int(timestamp) / 1000.0)
            return dt.strftime("%Y-%m-%d")
        except:
            return None

    def handle(self, *args, **options):
        self.populate_parties_cache()

        data_dir = Path(options["data_path"])

        # spending_dir = data_dir / "Spending"
        # for file in spending_dir.glob("**/*.json"):
        #     data = json.load(file.open())
        #     self.add_spending(data=data)

        # accounts_dir = data_dir / "Accounts"
        # for file in accounts_dir.glob("**/*.json"):
        #     data = json.load(file.open())
        #     self.add_accounts(data=data)

        donations_dir = data_dir / "Donations"
        for file in donations_dir.glob("**/*.json"):
            data = json.load(file.open())
            donation = self.add_donations(data=data)
            print(donation)
