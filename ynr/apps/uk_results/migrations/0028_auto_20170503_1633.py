from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [("uk_results", "0027_auto_20170502_2130")]

    operations = [
        migrations.RenameField(
            model_name="council", old_name="mapit_id", new_name="slug"
        )
    ]
