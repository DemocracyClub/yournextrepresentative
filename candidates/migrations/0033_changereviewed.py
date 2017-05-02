# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        ('popolo', '0002_update_models_from_upstream'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('candidates', '0032_migrate_org_slugs'),
    ]

    operations = [
        migrations.CreateModel(
            name='ChangeReviewed',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('logged_action', models.ForeignKey(to='candidates.LoggedAction')),
                ('person', models.ForeignKey(to='popolo.Person')),
                ('reviewer', models.ForeignKey(to=settings.AUTH_USER_MODEL)),
            ],
        ),
    ]
