from candidates.models import Ballot
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError
from people.models import Person
from splitting.splitter import PersonSplitter


class Command(BaseCommand):
    help = """
    Move a candidacy that's been attached to the wrong person to a new person,
    or to an existing person with --to-person.

    Only shows what would happen unless --commit is given.

    Prints a one-row, tab-separated report (Person URL, Person ID, Ballot,
    Destination person ID, Result, Notes) that can be pasted into a sheet.
    Use --details to see the full plan.
    """

    def add_arguments(self, parser):
        parser.add_argument("person_id", type=int)
        parser.add_argument("ballot_paper_id")
        parser.add_argument(
            "--to-person",
            type=int,
            help="Move the candidacy to this existing person",
        )
        parser.add_argument(
            "--username",
            help="The user to record the split against",
        )
        parser.add_argument(
            "--allow-locked",
            action="store_true",
            help="Allow splitting a candidacy on a locked ballot",
        )
        parser.add_argument(
            "--commit",
            action="store_true",
            help="Make the changes, rather than only showing them",
        )
        parser.add_argument(
            "--details",
            action="store_true",
            help="Also show the full plan",
        )
        parser.add_argument(
            "--no-header",
            action="store_true",
            help="Leave out the report's header row, for pasting several runs",
        )

    def get_object(self, model, **kwargs):
        try:
            return model.objects.get(**kwargs)
        except model.DoesNotExist:
            raise CommandError(f"{model.__name__} matching {kwargs} not found")

    def handle(self, *args, **options):
        person = self.get_object(Person, pk=options["person_id"])
        ballot = self.get_object(
            Ballot, ballot_paper_id=options["ballot_paper_id"]
        )
        target_person = None
        if options["to_person"]:
            target_person = self.get_object(Person, pk=options["to_person"])
        user = None
        if options["username"]:
            user = self.get_object(
                get_user_model(), username=options["username"]
            )

        splitter = PersonSplitter(
            person,
            ballot,
            target_person=target_person,
            user=user,
            allow_locked=options["allow_locked"],
        )
        plan = splitter.plan()
        if options["details"]:
            self.show_plan(plan)
        header = not options["no_header"]

        if not plan.is_valid:
            self.report(plan, "Can't split", header=header)
            raise CommandError("\n".join(plan.errors))

        if not options["commit"]:
            self.report(plan, "Ready to split", header=header)
            return

        target = splitter.split()
        self.report(plan, "Split", header=header, target=target)

    REPORT_COLUMNS = [
        "Person URL",
        "Person ID",
        "Ballot",
        "Destination person ID",
        "Result",
        "Notes",
    ]

    def report(self, plan, result, header=True, target=None):
        """
        One tab-separated row, with the same first columns as the sheet
        split requests are tracked in, so it can be pasted straight in
        """
        person = plan.person
        row = [
            f"{settings.BASE_URL}{person.get_absolute_url()}",
            str(person.pk),
            plan.membership.ballot.ballot_paper_id if plan.membership else "",
            plan.destination_label(target),
            result,
            "; ".join(self.notes(plan)),
        ]
        if header:
            self.stdout.write("\t".join(self.REPORT_COLUMNS))
        self.stdout.write("\t".join(row))

    @staticmethod
    def notes(plan):
        return plan.notes

    def show_plan(self, plan):
        for change in plan.changes:
            self.stdout.write(f"  * {change}")

        for warning in plan.warnings:
            self.stdout.write(self.style.WARNING(f"  ! {warning}"))
