import csv
import os

from django.core.management.base import BaseCommand

import resultsbot
from elections.models import Election


class Command(BaseCommand):
    def handle(self, **options):
        """
        Stores possible modgov urls stored in CSV file against the related election objects
        """

        # remove existing values first as this allows us to remove bad urls from the csv file
        Election.objects.update(modgov_url=None)

        path = os.path.join(
            os.path.dirname(resultsbot.__file__), "election_id_to_url.csv"
        )
        with open(path) as f:
            csv_file = csv.reader(f)
            for line in csv_file:
                try:
                    election = Election.objects.get(slug=line[0])
                    election.modgov_url = line[1]
                    election.save()
                except (IndexError, Election.DoesNotExist):
                    continue
