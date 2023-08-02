from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("results", "0002_resultevent_parlparse_id")]

    operations = [
        migrations.AddField(
            model_name="resultevent",
            name="post_name",
            field=models.CharField(max_length=1024, null=True, blank=True),
            preserve_default=True,
        )
    ]
