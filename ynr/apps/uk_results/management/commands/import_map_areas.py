import os
import csv
from datetime import date

import requests

from django.core.management.base import BaseCommand
from django.conf import settings
from slugify import slugify

from uk_results.models import CouncilElection, ElectionArea
from uk_results.constants import RESULTS_DATE

class Command(BaseCommand):
    EE_BASE_URL = getattr(
        settings, "EE_BASE_URL", "https://elections.democracyclub.org.uk/")


    def get_geo_json_from_ee(self, council_id):
        req = requests.get("{}api/organisations/{}/geo".format(
            self.EE_BASE_URL,
            council_id
        ))

        return req.content

    def handle(self, **options):
        qs = CouncilElection.objects.filter(
            election__election_date=RESULTS_DATE)
        self.import_council_areas(qs)
        self.import_concil_wards(qs)

    def import_council_areas(self, qs):
        for council_election in qs:

            geojson = self.get_geo_json_from_ee(council_election.council.pk)
            ElectionArea.objects.update_or_create(
                area_gss=council_election.council.pk,
                election=council_election.election,
                parent=None,
                area_name=council_election.council.name,
                defaults={
                    'geo_json': geojson
                }
            )

    def import_concil_wards(self, qs):
        """
        This is disabled for the moment, pending an API being added to EE
        to expose division geographies
        """
        return

