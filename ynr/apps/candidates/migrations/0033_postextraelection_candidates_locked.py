from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [("candidates", "0032_migrate_org_slugs")]

    operations = [
        migrations.AddField(
            model_name="postextraelection",
            name="candidates_locked",
            field=models.BooleanField(default=False),
        )
    ]
