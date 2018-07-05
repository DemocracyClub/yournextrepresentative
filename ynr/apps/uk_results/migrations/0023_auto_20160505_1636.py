# -*- coding: utf-8 -*-


from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('uk_results', '0022_postresult_confirmed_resultset'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='candidateresult',
            options={'ordering': ('-num_ballots_reported',)},
        ),
    ]
