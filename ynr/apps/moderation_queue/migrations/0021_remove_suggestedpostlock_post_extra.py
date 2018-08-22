from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [("moderation_queue", "0020_postextraelection_not_null")]

    operations = [
        migrations.RemoveField(
            model_name="suggestedpostlock", name="post_extra"
        )
    ]
