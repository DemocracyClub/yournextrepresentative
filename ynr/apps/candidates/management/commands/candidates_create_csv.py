from django.core.management.base import BaseCommand, CommandError
from django.core.files.storage import DefaultStorage
from django.db import reset_queries

from candidates.csv_helpers import list_to_csv
from candidates.models import PersonRedirect
from candidates.models.fields import get_complex_popolo_fields
from elections.models import Election
from people.models import Person

FETCH_AT_A_TIME = 1000


def queryset_iterator(qs, complex_popolo_fields):
    # To save building up a huge list of queries when DEBUG = True,
    # call reset_queries:
    reset_queries()
    start_index = 0
    while True:
        chunk_qs = qs.order_by("pk")[
            start_index : start_index + FETCH_AT_A_TIME
        ]
        empty = True
        for person in chunk_qs.joins_for_csv_output():
            empty = False
            person.complex_popolo_fields = complex_popolo_fields
            yield person
        if empty:
            return
        start_index += FETCH_AT_A_TIME


def safely_write(output_filename, people, group_by_post):
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

    csv = list_to_csv(people, group_by_post)
    file_store = DefaultStorage()
    with file_store.open(output_filename, "w") as out_file:
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

    def get_people(self, election, qs):
        all_people = []
        elected_people = []
        for person in queryset_iterator(qs, self.complex_popolo_fields):
            for d in person.as_list_of_dicts(
                election,
                base_url=self.options["site_base_url"],
                redirects=self.redirects,
            ):
                all_people.append(d)
                if d["elected"] == "True":
                    elected_people.append(d)
        return all_people, elected_people

    def handle(self, **options):
        if options["election"]:
            try:
                all_elections = [Election.objects.get(slug=options["election"])]
            except Election.DoesNotExist:
                message = "Couldn't find an election with slug {election_slug}"
                raise CommandError(
                    message.format(election_slug=options["election"])
                )
        else:
            all_elections = list(Election.objects.all()) + [None]

        self.options = options
        self.complex_popolo_fields = get_complex_popolo_fields()
        self.redirects = PersonRedirect.all_redirects_dict()
        self.output_prefix = "candidates"

        for election in all_elections:
            if election is None:
                # Get information for every candidate in every
                # election.
                qs = Person.objects.all()
                all_people, elected_people = self.get_people(election, qs)
                output_filenames = {
                    "all": self.output_prefix + "-all.csv",
                    "elected": self.output_prefix + "-elected-all.csv",
                }
            else:
                # Only get the candidates standing in that particular
                # election
                role = election.candidate_membership_role
                qs = Person.objects.filter(
                    memberships__post_election__election=election,
                    memberships__role=role,
                )
                all_people, elected_people = self.get_people(election, qs)
                output_filenames = {
                    "all": self.output_prefix + "-" + election.slug + ".csv",
                    "elected": self.output_prefix
                    + "-elected-"
                    + election.slug
                    + ".csv",
                }
            group_by_post = election is not None
            safely_write(output_filenames["all"], all_people, group_by_post)
            safely_write(
                output_filenames["elected"], elected_people, group_by_post
            )
