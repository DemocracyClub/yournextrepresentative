# Generated by Django 3.2.12 on 2022-05-25 09:37

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [("candidates", "0081_alter_loggedaction_action_type")]

    operations = [
        migrations.AlterField(
            model_name="ballot",
            name="winner_count",
            field=models.PositiveSmallIntegerField(blank=True, default=1),
        )
    ]