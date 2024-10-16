from datetime import date, timedelta

from candidates.models import Ballot
from dateutil.parser import parse
from django.core.management import CommandError
from django.core.management.base import BaseCommand
from django.db import transaction
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
        parser.add_argument(
            "--recently-updated-delta",
            dest="recently_updated_delta",
            action="store",
            type=int,
            help="Subtract this many hours from the recently updated time used by `--recently-updated`",
        )
        parser.add_argument(
            "--check-current",
            dest="check_current",
            action="store_true",
            help="Check that current elections are still marked as such in EE and verified the 'current' ballots",
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
                # check the parent election already exists in the DB and if it
                # doesn't allow an exception to be raised
                Election.objects.get(slug=election_dict.parent)
                # otherwise set parent to None as the KeyError indicates it is
                # not in the election tree because there is nothing to update
                parent = None

            election_dict.get_or_create_ballot(parent=parent)

    def check_local_current_against_remote(self):
        """
        Don't rely on EE's modified date, as the sliding 'current'
        window in EE doesn't update election objects.

        Rather, grab elections we think might no longer be current
        and check with EE
        """
        might_not_be_current = Election.objects.past().current()
        for election in might_not_be_current:
            importer = EveryElectionImporter(election_id=election.slug)
            importer.build_election_tree()
            current = importer.election_tree[election.slug].get("current")
            if not current:
                election.current = False
                election.save()

        # Now get all EE current elections and count them against the local DB.
        ee_importer = EveryElectionImporter(
            {"current": 1, "identifier_type": "ballot"}
        )
        ee_current_ballots = ee_importer.count_results()
        local_current_ballots = Ballot.objects.filter(
            election__current=True
        ).count()
        assert (
            ee_current_ballots == local_current_ballots
        ), f"Local and EE current ballots don't match EE: {ee_current_ballots} Local: {local_current_ballots}"

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
        ee_importer.build_election_tree(deleted=True)

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
            latest_ee_modified = self.get_latest_ee_modified_datetime()
            if hours := options["recently_updated_delta"]:
                latest_ee_modified = latest_ee_modified - timedelta(hours=hours)
            recently_updated_timestamp = latest_ee_modified.isoformat()

        if (
            options["recently_updated_delta"]
            and not options["recently_updated"]
        ):
            raise CommandError(
                "--recently-updated-delta only works with --recently-updated"
            )

        with transaction.atomic():
            if options["check_current"]:
                return self.check_local_current_against_remote()

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
            return None
