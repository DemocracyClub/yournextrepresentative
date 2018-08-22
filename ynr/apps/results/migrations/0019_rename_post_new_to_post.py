from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [("results", "0018_fix_2015_resultevent_winners")]

    operations = [
        migrations.RenameField(
            model_name="resultevent", old_name="post_new", new_name="post"
        )
    ]
