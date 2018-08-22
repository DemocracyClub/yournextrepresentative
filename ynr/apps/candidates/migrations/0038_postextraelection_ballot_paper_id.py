from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [("candidates", "0037_auto_20170510_2200")]

    operations = [
        migrations.AddField(
            model_name="postextraelection",
            name="ballot_paper_id",
            field=models.CharField(max_length=255, blank=True),
        )
    ]
