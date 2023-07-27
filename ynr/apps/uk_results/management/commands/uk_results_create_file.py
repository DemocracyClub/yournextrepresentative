import json
from collections import defaultdict

from django.core.files.base import ContentFile
from django.core.files.storage import DefaultStorage
from django.core.management.base import BaseCommand
from django.db.models import Prefetch
from popolo.models import Membership
from uk_results.models import ResultSet
from utils.dict_io import BufferDictWriter


class Command(BaseCommand):
    FIELDNAMES = [
        "election_id",
        "ballot_paper_id",
        "person_id",
        "party_id",
        "party_name",
        "person_name",
        "ballots_cast",
        "elected",
        "spoilt_ballots",
        "turnout",
        "turnout_percentage",
        "total_electorate",
        "source",
    ]

    def add_arguments(self, parser):
        parser.add_argument("--election-date", action="store", required=True)

        parser.add_argument(
            "--format", action="store", required=True, choices=["csv", "json"]
        )

    def handle(self, **options):
        date = options["election_date"]
        format = options["format"]
        directory_path = "csv-archives"
        self.storage = DefaultStorage()
        output_filename = "{}/results-{}.{}".format(
            directory_path, date, format
        )

        qs = (
            ResultSet.objects.filter(ballot__election__election_date=date)
            .select_related("ballot", "ballot__election")
            .prefetch_related(
                Prefetch(
                    "ballot__membership_set",
                    Membership.objects.select_related("person", "party"),
                )
            )
        )
        out_data = []
        for result in qs:

            for membership in result.ballot.membership_set.all():
                if not hasattr(membership, "result"):
                    continue
                row = {
                    "election_id": result.ballot.election.slug,
                    "ballot_paper_id": result.ballot.ballot_paper_id,
                    "turnout": result.num_turnout_reported,
                    "turnout_percentage": result.turnout_percentage,
                    "spoilt_ballots": result.num_spoilt_ballots,
                    "total_electorate": result.total_electorate,
                    "source": result.source,
                }
                party = membership.party
                try:
                    if party.name == "Independent":
                        party_id = "ynmp-party:2"
                    else:
                        party_id = (
                            party.identifiers.filter(
                                scheme="electoral-commission"
                            )
                            .get()
                            .identifier
                        )
                except membership.party.DoesNotExist:
                    party_id = ""
                row["party_id"] = party_id
                row["party_name"] = party.name
                row["person_id"] = membership.person.pk
                row["person_name"] = membership.person.name
                row["ballots_cast"] = membership.result.num_ballots
                row["elected"] = membership.elected
                out_data.append(row)

        if format == "csv":
            csv_out = BufferDictWriter(fieldnames=self.FIELDNAMES)
            csv_out.writeheader()
            for row in out_data:
                csv_out.writerow(row)
            out_string = csv_out.output
        else:
            json_data = defaultdict(dict)
            for person in out_data:
                election_dict = json_data[person["ballot_paper_id"]]
                election_dict["turnout"] = person["turnout"]
                election_dict["turnout_percentage"] = person[
                    "turnout_percentage"
                ]
                election_dict["spoilt_ballots"] = person["spoilt_ballots"]
                election_dict["total_electorate"] = person["total_electorate"]
                election_dict["source"] = person["source"]

                if "candidates" not in election_dict:
                    election_dict["candidates"] = []
                election_dict["candidates"].append(
                    {
                        "person_name": person["person_name"],
                        "person_id": person["person_id"],
                        "party_name": person["party_name"],
                        "party_id": person["party_id"],
                        "ballots_cast": person["ballots_cast"],
                        "elected": person["elected"],
                    }
                )
                election_dict["candidates"] = sorted(
                    election_dict["candidates"],
                    key=lambda p: p["ballots_cast"],
                    reverse=True,
                )
            out_string = json.dumps(json_data, indent=4)

        self.storage.save(
            output_filename, ContentFile(out_string.encode("utf8"))
        )
