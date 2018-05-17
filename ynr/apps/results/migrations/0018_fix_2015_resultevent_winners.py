# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations


def fix_2015_winners(apps, schema_editor):
    ResultEvent = apps.get_model('results', 'ResultEvent')
    Person = apps.get_model('popolo', 'Person')
    for re in ResultEvent.objects.filter(election__slug=2015):
        # Through some mistake or other, all the winners of the 2015
        # were set to the person with ID 1. Find the right person
        # instead:
        if re.winner.id == 1:
            re.winner = Person.objects.get(
                memberships__extra__elected=True,
                memberships__extra__post_election__election=re.election,
                memberships__post=re.post_new,
                memberships__on_behalf_of=re.winner_party)
            re.save()


class Migration(migrations.Migration):

    dependencies = [
        ('results', '0017_rename_post_name_to_old_post_name'),
    ]

    operations = [
        migrations.RunPython(fix_2015_winners),
    ]
