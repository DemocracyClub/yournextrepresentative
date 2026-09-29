from candidates.models import Ballot
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError
from people.models import Person
from splitting.provenance import COMPARABLE_FIELDS, DEFAULT_CUTOFF_DAYS
from splitting.splitter import PersonSplitter


def show_value(value, width=30):
    if isinstance(value, tuple):
        value = ", ".join(value)
    if not value:
        return "(nothing)"
    value = str(value).replace("\n", " ")
    if len(value) > width:
        value = value[: width - 1] + "…"
    return f'"{value}"'


class Command(BaseCommand):
    help = """
    Move a candidacy that's been attached to the wrong person to a new person,
    or to an existing person with --to-person.

    With --suggest, also work out where the candidacy came from and suggest
    what else to move. If it arrived in a merge, the merged-away person is
    restored.

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
            "--suggest",
            action="store_true",
            help=(
                "Use the person's history to suggest what else to move, "
                "restoring a merged-away person where possible"
            ),
        )
        parser.add_argument(
            "--cutoff-days",
            type=int,
            default=DEFAULT_CUTOFF_DAYS,
            help=(
                "With --suggest, only restore identifiers and biographies "
                "set within this many days (default %(default)s)"
            ),
        )
        parser.add_argument(
            "--move-field",
            action="append",
            default=[],
            metavar="FIELD",
            help="With --suggest, move this field's current value (repeatable)",
        )
        parser.add_argument(
            "--keep-field",
            action="append",
            default=[],
            metavar="FIELD",
            help="With --suggest, keep this field on the person (repeatable)",
        )
        parser.add_argument(
            "--move-image",
            action="store_true",
            help="With --suggest, move the person's photo too",
        )
        parser.add_argument(
            "--commit",
            action="store_true",
            help="Make the changes, rather than only showing them",
        )
        parser.add_argument(
            "--details",
            action="store_true",
            help="Also show the full plan: where each detail goes and why",
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
        for name in options["move_field"] + options["keep_field"]:
            if name not in COMPARABLE_FIELDS:
                raise CommandError(
                    f"Unknown field '{name}'. Choose from: "
                    f"{', '.join(COMPARABLE_FIELDS)}"
                )

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
            suggest=options["suggest"],
            cutoff_days=options["cutoff_days"],
            move_fields=options["move_field"],
            keep_fields=options["keep_field"],
            move_image=options["move_image"],
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
        notes = plan.notes
        if plan.details_to_check:
            notes.append(
                f"{len(plan.details_to_check)} detail(s) need checking: run "
                "with --details"
            )
        return notes

    def show_plan(self, plan):
        origin = plan.origin
        if origin and origin.add_version:
            when = origin.added_at.date().isoformat()
            if origin.kind == "merge":
                self.stdout.write(
                    f"Origin: merged from person {origin.merged_from} on "
                    f"{when} (by {origin.added_by})"
                )
            else:
                self.stdout.write(
                    f"Origin: added directly on {when} (by {origin.added_by})"
                )
        elif origin:
            self.stdout.write("Origin: unknown")

        for change in plan.changes:
            self.stdout.write(f"  * {change}")

        shown = [s for s in plan.field_suggestions if s.notable]
        if shown:
            other = plan.restore_person_id or "new"
            original = plan.person.pk
            self.stdout.write("Fields:")
            for s in shown:
                if s.dest_value == s.current_value:
                    dest = f"{original} keeps {show_value(s.dest_value)}"
                else:
                    dest = f"{original} -> {show_value(s.dest_value)}"
                line = (
                    f"  {s.action.upper():<8}{s.field:<22}"
                    f"{other} <- {show_value(s.target_value):<34}| {dest}"
                    f"  ({s.reason})"
                )
                style = self.style.WARNING if s.action == "review" else str
                self.stdout.write(style(line))

        for warning in plan.warnings:
            self.stdout.write(self.style.WARNING(f"  ! {warning}"))
