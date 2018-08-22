from django.core.management.base import BaseCommand

from popolo.models import Membership

from popolo.models import Person


class Command(BaseCommand):

    help = "Find elections in not_standing that should be removed"

    def add_arguments(self, parser):
        parser.add_argument(
            "--delete",
            action="store_true",
            help="Don't just find these broken cases, also fix them",
        )

    def handle(self, *args, **options):
        for person in Person.objects.filter(not_standing__isnull=False):
            election_to_remove = []
            for election in person.not_standing.all():
                candidacies = Membership.objects.filter(
                    person=person,
                    extra__election=election,
                    role=election.candidate_membership_role,
                )
                if candidacies.exists():
                    election_to_remove.append(election)
            # Now print out the elections we would remove from
            # not_standing for that person.  (And, if --delete is
            # specified, actually remove it.)
            for election in election_to_remove:
                fmt = "{person} is marked as not standing in {election}"
                print(fmt.format(person=person, election=election))
                print("  ... but also has a candidacy in that election!")
                if options["delete"]:
                    fmt = "  Deleting {election} from {person}'s not_standing"
                    print(
                        fmt.format(election=election.name, person=person.name)
                    )
                    person.not_standing.remove(election)
