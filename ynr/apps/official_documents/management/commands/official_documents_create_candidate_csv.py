from django.core.management.base import BaseCommand
from official_documents.models import OfficialDocument
from popolo.models import Membership
from utils.dict_io import BufferDictWriter


class Command(BaseCommand):
    help = "Create a CSV with candidate info form the SOPNs"

    def handle(self, *args, **options):
        fieldnames = (
            "election_id",
            "division_id",
            "division_name",
            "candidate_id",
            "candidate_name",
            "candidate_other_names",
            "party_id",
            "party_name",
            "document_id",
        )
        out_csv = BufferDictWriter(fieldnames)
        out_csv.writeheader()
        documents = OfficialDocument.objects.all().order_by("election", "post")
        for document in documents:
            document_memberships = Membership.objects.filter(
                post=document.post, election=document.election
            ).select_related("base", "party", "post", "person")

            out_dict = {
                "election_id": document.election.slug,
                "division_id": document.post.slug,
                "division_name": document.post.short_label,
                "document_id": document.pk,
            }

            for membership in document_memberships:
                other_names = "|".join(
                    [o.name for o in membership.base.person.other_names.all()]
                )
                party = membership.party

                out_dict.update(
                    {
                        "candidate_id": membership.base.person.id,
                        "candidate_name": membership.base.person.name,
                        "candidate_other_names": other_names,
                        "party_id": party.ec_id,
                        "party_name": party.name,
                    }
                )

                out_csv.writerow(out_dict)
            else:
                out_csv.writerow(out_dict)

        self.stdout.write(out_csv.output)
