from collections import defaultdict

from django.core.files.storage import DefaultStorage
from django.core.management.base import BaseCommand, CommandError

from candidates.csv_helpers import list_to_csv, memberships_dicts_for_csv
from elections.models import Election


def safely_write(output_filename, memberships_list):
    """
    Use Django's storage backend to write the CSV file to the MEDIA_ROOT.

    If using S3 (via Django Storages) the file is atomically written when the
    file is closed (when the context manager closes).

    That is, the file can be opened and written to but nothing changes at
    the public S3 URL until the object is closed. Meaning it's not possible to
    have a half written file.

    If not using S3, there will be a short time where the file is empty
    during write.
    """

    csv = list_to_csv(memberships_list)
    file_store = DefaultStorage()
    with file_store.open(output_filename, "wb") as out_file:
        out_file.write(csv.encode("utf-8"))


class Command(BaseCommand):

    help = "Output CSV files for all elections"

    def add_arguments(self, parser):
        parser.add_argument(
            "--site-base-url",
            help="The base URL of the site (for full image URLs)",
        )
        parser.add_argument(
            "--election",
            metavar="ELECTION-SLUG",
            help="Only output CSV for the election with this slug",
        )

    def slug_to_file_name(self, slug):
        return "{}-{}.csv".format(self.output_prefix, slug)

    def handle(self, **options):
        if options["election"]:
            try:
                election = Election.objects.get(slug=options["election"])
                election_slug = election.slug
            except Election.DoesNotExist:
                message = "Couldn't find an election with slug {election_slug}"
                raise CommandError(
                    message.format(election_slug=options["election"])
                )
        else:
            election_slug = None

        self.options = options
        self.output_prefix = "candidates"

        membership_by_election, elected_by_election = memberships_dicts_for_csv(
            election_slug
        )
        # Write a file per election, optionally adding candidates
        # We still want a file to exist if there are no candidates yet,
        # as the files linked to as soon as the election is created
        election_qs = Election.objects.all()
        if election_slug:
            election_qs = election_qs.filter(slug=election_slug)
        for election in election_qs:
            safely_write(
                self.slug_to_file_name(election.slug),
                membership_by_election.get(election.slug, []),
            )

        # Make a CSV file per election date
        slugs_by_date = defaultdict(list)
        for slug in membership_by_election.keys():
            slugs_by_date[slug.split(".")[-1]].append(slug)
        for date, slugs in slugs_by_date.items():
            memberships_for_date = []
            for slug in slugs:
                memberships_for_date += membership_by_election[slug]
            safely_write(self.slug_to_file_name(date), memberships_for_date)

        # If we're not outputting a single election, output all elections
        if not election_slug:
            sorted_elections = sorted(
                membership_by_election.keys(),
                key=lambda key: key.split(".")[-1],
            )
            all_memberships = []
            all_elected = []
            for slug in sorted_elections:
                all_memberships += membership_by_election[slug]
                all_elected += elected_by_election[slug]
            safely_write(self.slug_to_file_name("all"), all_memberships)
            safely_write(self.slug_to_file_name("elected-all"), all_elected)
