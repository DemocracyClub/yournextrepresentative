from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [("uk_results", "0020_auto_20160503_1920")]

    operations = [
        migrations.RenameField(
            model_name="councilelection",
            old_name="controller",
            new_name="controller_resultset",
        )
    ]
