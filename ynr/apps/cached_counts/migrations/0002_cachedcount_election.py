# -*- coding: utf-8 -*-


from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('cached_counts', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='cachedcount',
            name='election',
            field=models.CharField(max_length=512, null=True, blank=True),
            preserve_default=True,
        ),
    ]
