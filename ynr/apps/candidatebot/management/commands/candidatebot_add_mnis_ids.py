import json
from dataclasses import dataclass
from pathlib import Path
from typing import Type, TypeVar

import requests
from django.core.management.base import BaseCommand

from candidatebot.helpers import CandidateBot
from people.models import Person


T_WikiDataPerson = TypeVar("T_WikiDataPerson", bound="WikiDataPerson")


@dataclass
class WikiDataPerson:
    wikidata_id: str
    mnis_id: str
    ynr_id: str

    @classmethod
    def from_wikidata_query(
        cls: Type[T_WikiDataPerson], wikidata_json
    ) -> T_WikiDataPerson:
        return cls(
            wikidata_id=wikidata_json["person"]["value"].split("/")[-1],
            mnis_id=wikidata_json["mnisID"]["value"],
            ynr_id=wikidata_json["dc"]["value"],
        )

    def update_ynr_person(self):
        person = Person.objects.get_by_id_with_redirects(self.ynr_id)
        bot = CandidateBot(person.pk, ignore_errors=True)
        bot.add_mnis_id(self.mnis_id)
        bot.add_wikidata_id(self.wikidata_id)
        bot.save(source="Wikidata")
        if bot.edits_made:
            return f"Updated person {person.pk} with MNIS ID {self.mnis_id}"


class WikidataHelper:
    MNIS_IDS_QUERY = """
    SELECT DISTINCT ?mnisID ?person ?personLabel ?dc WHERE
    {
    # Filters
    # person is a person
      ?person wdt:P31 wd:Q5 .
    # person has a MNIS ID
      ?person wdt:P10428 ?mnisID .
    # person DC ID
      ?person  wdt:P6465 ?dc .

    SERVICE wikibase:label { bd:serviceParam wikibase:language "en". }

    }
    """

    def get_objects_with_mnis_ids(self, cache=True):
        cache_file = Path("wikidata_cache.json")
        if cache and cache_file.exists():
            return json.loads(cache_file.read_text())
        params = {"format": "json", "query": self.MNIS_IDS_QUERY}
        req = requests.get(
            "https://query.wikidata.org/bigdata/namespace/wdq/sparql",
            params=params,
        )
        req.raise_for_status()
        results = req.json()["results"]["bindings"]
        if cache:
            cache_file.write_text(json.dumps(results, indent=4))
        return results


class Command(BaseCommand):
    help = """
    MNIS — the Members' Names Information Service from the UK Parliament

    These are IDs for members of Parliament. They are used in all their internal systems
    for various reasons.

    The Parliament Library have also added them to WikiData and matched them to DC
    person IDs.

    This management command pulls the IDs from WikiData and creates IDs for them
    against the person.
    """

    def handle(self, *args, **options):
        wikidata = WikidataHelper()
        for result in wikidata.get_objects_with_mnis_ids():
            wikidata_person = WikiDataPerson.from_wikidata_query(result)
            if output := wikidata_person.update_ynr_person():
                self.stdout.write(output)
