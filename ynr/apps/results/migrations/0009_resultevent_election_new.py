# -*- coding: utf-8 -*-


from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('elections', '0012_election_people_elected_per_post'),
        ('results', '0008_remove_resultevent_winner_popit_person_id'),
    ]

    operations = [
        migrations.AddField(
            model_name='resultevent',
            name='election_new',
            field=models.ForeignKey(blank=True, to='elections.Election', null=True),
        ),
    ]
