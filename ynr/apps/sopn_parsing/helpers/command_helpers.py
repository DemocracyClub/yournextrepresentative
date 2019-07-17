from django.core.management.base import BaseCommand

from candidates.models import Ballot


class BaseSOPNParsingCommand(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument(
            "--ballot", action="store", help="Parse tables for a single ballot"
        )
        parser.add_argument(
            "--current",
            action="store_true",
            help="Only process current ballots",
        )
        parser.add_argument(
            "--reparse",
            action="store_true",
            help="Reparse documents that have already been parsed",
        )

    def get_queryset(self, options):
        filter_kwargs = {}
        if options.get("ballot"):
            filter_kwargs["ballot_paper_id"] = options["ballot"]

        if options["current"]:
            filter_kwargs["election__current"] = True

        qs = Ballot.objects.all()
        qs = qs.filter(**filter_kwargs)
        qs = qs.exclude(officialdocument=None)
        return qs
