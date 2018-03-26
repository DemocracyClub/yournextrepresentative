from django.core.management.base import BaseCommand

from candidates.models import PostExtraElection



class Command(BaseCommand):
    def output_results_csv_for_date(self, date):
        output = []
        # First get all the Post Elections we care about
        pees = PostExtraElection.objects.filter(election__election_date=date)

        # for each post election, get the slug and memberships,
        for pee in pees:
            election_slug = pee.election.slug

            # for each membership get the person ID and name
            for membership in pee.postextra.base.memberships.all():
                person_name = membership.person.name
                person_id = membership.person.pk

                # Add everything to the output
                output.append([
                    election_slug,
                    person_name,
                    person_id
                ])
        for line in output:
            print "\t".join([str(x) for x in line])

    def add_arguments(self, parser):
        parser.add_argument('date', type=str)


    def handle(self, **options):
        self.output_results_csv_for_date(options['date'])
