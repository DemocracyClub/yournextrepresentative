# Generated by Django 4.1.7 on 2023-05-04 20:41

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("uk_results", "0056_remove_candidateresult_is_winner"),
    ]

    operations = [
        migrations.AddField(
            model_name="candidateresult",
            name="rank",
            field=models.PositiveIntegerField(
                null=True, verbose_name="Results Rank"
            ),
        ),
    ]
