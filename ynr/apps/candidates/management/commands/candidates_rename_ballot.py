"""
Foo Bar

"""
import sys

from argparse import ArgumentParser
from django.core.management import BaseCommand
from django.db import transaction

from candidates.models import Ballot, LoggedAction
from candidates.models.popolo_extra import model_has_related_objects
from official_documents.models import OfficialDocument
from popolo.models import Membership
from uk_results.models import ResultSet


class BallotMover:
    def __init__(self, old_id: str, new_id: str, stdout=None) -> None:
        if not stdout:
            stdout = sys.stdout()
        self.stdout = stdout
        self.old_ballot = Ballot.objects.get(ballot_paper_id=old_id)
        self.new_ballot = Ballot.objects.get(ballot_paper_id=new_id)

    @transaction.atomic()
    def move(self, confirm=True):
        """
        Main command to move ballots
        """

        self.move_memberships()
        self.move_logged_actions()
        self.move_sopns()
        self.move_results()
        assert not model_has_related_objects(self.old_ballot)

    def move_simple(self, model):
        qs = model.objects.filter(ballot=self.old_ballot)
        updated = qs.update(ballot=self.new_ballot)
        self.stdout.write(
            f"Moved {updated} {model._meta.verbose_name_plural.title()}"
        )

    def move_memberships(self):
        self.move_simple(Membership)

    def move_logged_actions(self):
        self.move_simple(LoggedAction)

    def move_sopns(self):
        self.move_simple(OfficialDocument)

    def move_results(self):
        self.move_simple(ResultSet)


class Command(BaseCommand):
    help = """
    A management command for moving all objects attached to one ballot to another.

    This should only be used when the initial ballot was created incorrectly in EE
    and the objects need to be moved to the correct ID.

    NOTE: both ballots need to exist before the move can happen, this command doesn't create any objects,
    it only changes the FK of related objects.

    """

    def add_arguments(self, parser: ArgumentParser):
        parser.add_argument("--old", action="store", required=True)
        parser.add_argument("--new", action="store", required=True)

    def handle(self, *args, **options):
        mover = BallotMover(options["old"], options["new"], stdout=self.stdout)
        mover.move()
