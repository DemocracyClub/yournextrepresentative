from django.core.management.base import BaseCommand

from people.splitting import PersonCandidacySplitter


class Command(BaseCommand):
    help = "Split a person based on candidacy"

    def add_arguments(self, parser):
        parser.add_argument("--person_id", action="store")

    def handle(self, *args, **options):
        splitter = PersonCandidacySplitter(
            options["person_id"], stdout=self.stdout
        )
        splitter.split_on_candidacy = splitter.possible_candidacies[2]
        # splitter.candidacy_picker()

        splitter.find_version_to_revert_to()
