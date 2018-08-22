from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [("moderation_queue", "0006_auto_20150303_0838")]

    operations = [
        migrations.AlterField(
            model_name="queuedimage",
            name="why_allowed",
            field=models.CharField(
                default=b"other",
                max_length=64,
                choices=[
                    (
                        b"public-domain",
                        b"This photograph is free of any copyright restrictions",
                    ),
                    (
                        b"copyright-assigned",
                        b"I own copyright of this photo and I assign the copyright to Democracy Club Limited in return for it being displayed on YourNextMP",
                    ),
                    (
                        b"profile-photo",
                        b"This is the candidate's public profile photo from social media (e.g. Twitter, Facebook) or their official campaign page",
                    ),
                    (b"other", b"Other"),
                ],
            ),
            preserve_default=True,
        )
    ]
