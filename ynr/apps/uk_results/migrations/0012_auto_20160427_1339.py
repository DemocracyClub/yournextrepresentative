from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [("uk_results", "0011_auto_20160427_1305")]

    operations = [
        migrations.RenameField(
            model_name="resultset", old_name="post", new_name="post_result"
        )
    ]
