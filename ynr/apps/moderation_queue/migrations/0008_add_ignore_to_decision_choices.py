from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [("moderation_queue", "0007_auto_20150303_1420")]

    operations = [
        migrations.AlterField(
            model_name="queuedimage",
            name="decision",
            field=models.CharField(
                default=b"undecided",
                max_length=32,
                choices=[
                    (b"approved", b"Approved"),
                    (b"rejected", b"Rejected"),
                    (b"undecided", b"Undecided"),
                    (b"ignore", b"Ignore"),
                ],
            ),
            preserve_default=True,
        )
    ]
