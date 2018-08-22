from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [("results", "0016_rename_post_id_to_old_post_id")]

    operations = [
        migrations.RenameField(
            model_name="resultevent",
            old_name="post_name",
            new_name="old_post_name",
        )
    ]
