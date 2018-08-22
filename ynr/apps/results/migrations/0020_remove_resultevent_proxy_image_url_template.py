from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [("results", "0019_rename_post_new_to_post")]

    operations = [
        migrations.RemoveField(
            model_name="resultevent", name="proxy_image_url_template"
        )
    ]
