import django_extensions.db.fields
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [("official_documents", "0016_election_not_null")]

    operations = [
        migrations.AlterField(
            model_name="officialdocument",
            name="created",
            field=django_extensions.db.fields.CreationDateTimeField(
                auto_now_add=True, verbose_name="created"
            ),
        ),
        migrations.AlterField(
            model_name="officialdocument",
            name="modified",
            field=django_extensions.db.fields.ModificationDateTimeField(
                auto_now=True, verbose_name="modified"
            ),
        ),
    ]
