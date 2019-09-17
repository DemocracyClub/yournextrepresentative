from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [("candidates", "0034_candidates_locked_data")]

    operations = [
        migrations.RemoveField(model_name="postextra", name="candidates_locked")
    ]
