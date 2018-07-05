# -*- coding: utf-8 -*-


from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('results', '0015_rename_to_winner_party'),
    ]

    operations = [
        migrations.RenameField(
            model_name='resultevent',
            old_name='post_id',
            new_name='old_post_id',
        ),
    ]
