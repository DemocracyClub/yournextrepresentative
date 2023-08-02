from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("official_documents", "0003_add_group")]

    operations = [
        migrations.AlterField(
            model_name="officialdocument",
            name="document_type",
            field=models.CharField(
                max_length=100,
                choices=[(b"Nomination paper", b"Nomination paper")],
            ),
            preserve_default=True,
        )
    ]
