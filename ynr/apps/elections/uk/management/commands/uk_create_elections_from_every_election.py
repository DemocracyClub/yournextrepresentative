from datetime import date, timedelta

from django.core.management.base import BaseCommand
from django.db import transaction
from dateutil.parser import parse

from candidates.models import Ballot
from elections.models import Election
from elections.uk.every_election import EveryElectionImporter


class Command(BaseCommand):
    help = "Create posts and elections from a EveryElection"

    def add_arguments(self, parser):
        parser.add_argument(
            "--full",
            action="store_true",
            help="Do a full import of all elections",
        )
        parser.add_argument(
            "--poll-open-date",
            action="store",
            type=self.valid_date,
            help="Just import elections for polls that open on a given date",
        )
        parser.add_argument(
            "--recently-updated",
            dest="recently_updated",
            action="store_true",
            help="Only import elections that have been updated since last ee_modified date",
        )

    def valid_date(self, value):
        return parse(value).date()

    def get_latest_ee_modified_datetime(self):
        """
        Returns a timestamp of the last known update to an Election in
        EveryElection that has been stored against a Ballot or
        Election in our database.
        """
        ballots = Ballot.objects.ordered_by_latest_ee_modified()
        return ballots.first().latest_ee_modified

    def import_approved_elections(
        self, full=False, poll_open_date=None, recently_updated_timestamp=None
    ):
        # Get all approved elections from EveryElection
        query_args = None
        if full:
            query_args = {}
        if poll_open_date:
            query_args = {"poll_open_date": poll_open_date}

        if recently_updated_timestamp:
            query_args = {"modified": recently_updated_timestamp}

        ee_importer = EveryElectionImporter(query_args)
        ee_importer.build_election_tree()

        for ballot_id, election_dict in ee_importer.ballot_ids.items():

            try:
                parent = ee_importer.get_parent(ballot_id)
            except KeyError as e:
                # raise the exception if this is not a recent update
                if not recently_updated_timestamp:
                    raise e
                # otherwise set parent to None as the KeyError
                # indicates there is nothing to update on the parent
                # election which is why it is not in the election tree
                parent = None

            election_dict.get_or_create_ballot(parent=parent)

    def delete_deleted_elections(self, recently_updated_timestamp):
        # Get all deleted elections from EE
        params = {
            "poll_open_date__gte": str(date.today() - timedelta(days=30)),
            "deleted": 1,
        }
        if recently_updated_timestamp:
            params.pop("poll_open_date__gte")
            params["modified"] = recently_updated_timestamp

        ee_importer = EveryElectionImporter(params)

        # TODO account for -recently-updated flag herw?
        ee_importer.build_election_tree()

        for ballot_id, election_dict in ee_importer.ballot_ids.items():
            election_dict.delete_ballot()

        for group_id, election_dict in ee_importer.group_ids.items():
            election_dict.delete_election()

    def handle(self, *args, **options):
        current_only = not any(
            (
                options["full"],
                options["poll_open_date"],
                options["recently_updated"],
            )
        )
        recently_updated_timestamp = None
        if options["recently_updated"]:
            recently_updated_timestamp = (
                self.get_latest_ee_modified_datetime().isoformat()
            )

        with transaction.atomic():
            if current_only:
                # Mark all elections as not current, any that are current will
                # be (re)set later
                Election.objects.update(current=False)

            self.import_approved_elections(
                full=options["full"],
                poll_open_date=options["poll_open_date"],
                recently_updated_timestamp=recently_updated_timestamp,
            )
            self.delete_deleted_elections(
                recently_updated_timestamp=recently_updated_timestamp
            )
