from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ("moderation_queue", "0008_add_photo_review_permissions"),
        ("moderation_queue", "0008_add_ignore_to_decision_choices"),
    ]

    operations = []
