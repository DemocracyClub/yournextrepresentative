# -*- coding: utf-8 -*-


from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('popolo', '0002_update_models_from_upstream'),
        ('results', '0010_resultevent_winner_party_new'),
    ]

    operations = [
        migrations.AddField(
            model_name='resultevent',
            name='post_new',
            field=models.ForeignKey(blank=True, to='popolo.Post', null=True),
        ),
    ]
