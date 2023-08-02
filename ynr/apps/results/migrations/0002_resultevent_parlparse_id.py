from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("results", "0001_initial")]

    operations = [
        migrations.AddField(
            model_name="resultevent",
            name="parlparse_id",
            field=models.CharField(max_length=256, null=True, blank=True),
            preserve_default=True,
        )
    ]
