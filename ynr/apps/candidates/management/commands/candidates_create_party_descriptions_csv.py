from compat import BufferDictWriter

from django.core.management.base import BaseCommand

from official_documents.models import OfficialDocument
from popolo.models import Organization, Identifier


class Command(BaseCommand):

    help = "Create a CSV with candidate info form the SOPNs"

    def handle(self, *args, **options):
        fieldnames = ("party_id", "party_name", "party_description")
        out_csv = BufferDictWriter(fieldnames)
        out_csv.writeheader()

        for org in Organization.objects.filter(classification="Party"):
            try:
                party_id = org.identifiers.get(
                    scheme="electoral-commission"
                ).identifier
            except Identifier.DoesNotExist:
                party_id = org.identifiers.get(
                    scheme="popit-organization"
                ).identifier

            out_dict = {
                "party_id": party_id,
                "party_name": org.name,
                "party_description": "",
            }
            out_csv.writerow(out_dict)
            for desc in org.other_names.all():
                out_dict["party_description"] = desc.name
                out_csv.writerow(out_dict)

        self.stdout.write(out_csv.output)
