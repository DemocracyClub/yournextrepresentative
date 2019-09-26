from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [("moderation_queue", "0010_auto_add_crop_bounds")]

    operations = [
        migrations.AddField(
            model_name="queuedimage",
            name="face_detection_tried",
            field=models.BooleanField(default=False),
            preserve_default=True,
        )
    ]
