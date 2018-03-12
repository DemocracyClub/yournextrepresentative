# -*- coding: utf-8 -*-
from __future__ import print_function, unicode_literals

from compat import BufferDictWriter

from django.core.management.base import BaseCommand

from official_documents.models import OfficialDocument
from candidates.models import MembershipExtra
from popolo.models import Identifier


class Command(BaseCommand):

    help = "Create a CSV with candidate info form the SOPNs"

    def handle(self, *args, **options):
        import time
        start_time = time.time()
        fieldnames = (
            'election_id',
            'division_id',
            'division_name',
            'candidate_id',
            'candidate_name',
            'candidate_other_names',
            'party_id',
            'party_name',
            'document_id',
        )
        out_csv = BufferDictWriter(fieldnames)
        out_csv.writeheader()
        documents = OfficialDocument.objects.all().order_by('election', 'post')
        for document in documents:
            document_memberships = MembershipExtra.objects.filter(
                base__post=document.post,
                election=document.election
            ).select_related(
                'base',
                'base__on_behalf_of',
                'base__post__extra',
                'base__post',
                'base__person',
            )

            for membership in document_memberships:

                other_names = "|".join(
                    [o.name for o in membership.base.person.other_names.all()]
                )
                party = membership.base.on_behalf_of
                try:
                    party_id = party.identifiers.get(
                        scheme='electoral-commission').identifier
                except Identifier.DoesNotExist:
                    party_id = party.identifiers.get(
                        scheme='popit-organization').identifier

                out_dict = {
                    'election_id': membership.election.slug,
                    'division_id': membership.base.post.extra.slug,
                    'division_name': membership.base.post.extra.short_label,
                    'candidate_id': membership.base.person.id,
                    'candidate_name': membership.base.person.name,
                    'candidate_other_names': other_names,
                    'party_id': party_id,
                    'party_name': party.name,
                    'document_id': document.pk,
                }
                out_csv.writerow(out_dict)
        self.stdout.write(out_csv.output)
