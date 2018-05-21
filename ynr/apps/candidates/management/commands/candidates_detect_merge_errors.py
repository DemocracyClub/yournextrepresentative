# -*- coding: utf-8 -*-
from __future__ import print_function, unicode_literals

from django.db.models.deletion import Collector
from django.db import transaction
from django.core.management.base import BaseCommand
from django.db.models import Count

from popolo.models import Person, Membership
from candidates.models import MembershipExtra


class Command(BaseCommand):
    """
    There is a bug in merging the causes some people to have duplicate
    memberships. That is, a membership[extra] pair that joins the same
    (person, post_election) pair.

    This management command will detect them and optionally fix them by
    removing one of the duplicates.

    This only works if there are exactly 2 duplicate models, not more than 2.

    Running the command more than once will fix more than 2 duplicates, but
    so far none have been seen.
    """

    def add_arguments(self, parser):
        parser.add_argument(
            '--fix',
            action='store_true',
        )


    def handle(self, *args, **options):
        qs = Person.objects.all()
        qs = qs.values(
            'pk', 'memberships__post_election'
        ).annotate(
            pees=Count('memberships__post_election')
        ).filter(
            pees__gt=1
        )

        for row in qs:
            print("{} has {} duplicate post elections attached".format(
                row['pk'], row['pees']
            ))
            if options['fix']:
                with transaction.atomic():
                    duplicate_pee_pk = row['memberships__post_election']
                    membership = Membership.objects.filter(
                        post_election=duplicate_pee_pk,
                        person_id=row['pk'],
                    ).first()

                    membership_collector = Collector(using='default')
                    membership_extra_collector = Collector(using='default')
                    membership_collector.collect([membership])
                    membership_extra_collector.collect([membership.extra])


                    clean_membership_dependencies = [
                        o for o in
                        membership_collector.dependencies.items()[0][1]
                        if not issubclass(o, MembershipExtra)
                    ]

                    dependencies = any((
                        clean_membership_dependencies,
                        membership_extra_collector.dependencies,
                    ))

                    if not dependencies:
                        membership.extra.delete()
                        membership.delete()
                        print("Deleted a duplicate membership for {}".format(
                            row['pk']
                        ))
                    else:
                        print("Not deleting because of dependencies:")
                        print(membership_collector.dependencies)
                        print(membership_extra_collector.dependencies)
