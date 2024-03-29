# -*- coding: utf-8 -*-
# Generated by Django 1.10.8 on 2018-10-03 18:31
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("moderation_queue", "0022_add_detection_metadata")]

    operations = [
        migrations.AlterField(
            model_name="queuedimage",
            name="decision",
            field=models.CharField(
                choices=[
                    ("approved", "Approved"),
                    ("rejected", "Rejected"),
                    ("undecided", "Undecided"),
                    ("ignore", "Ignore"),
                ],
                default="undecided",
                max_length=32,
            ),
        ),
        migrations.AlterField(
            model_name="queuedimage",
            name="image",
            field=models.ImageField(
                max_length=512, upload_to="queued-images/%Y/%m/%d"
            ),
        ),
        migrations.AlterField(
            model_name="queuedimage",
            name="why_allowed",
            field=models.CharField(
                choices=[
                    (
                        "public-domain",
                        "This photograph is free of any copyright restrictions",
                    ),
                    (
                        "copyright-assigned",
                        "I own copyright of this photo and I assign the copyright to Democracy Club Limited in return for it being displayed on this site",
                    ),
                    (
                        "profile-photo",
                        "This is the candidate's public profile photo from social media (e.g. Twitter, Facebook) or their official campaign page",
                    ),
                    ("other", "Other"),
                ],
                default="other",
                max_length=64,
            ),
        ),
    ]
