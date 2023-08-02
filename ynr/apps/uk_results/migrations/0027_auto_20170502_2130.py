from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("uk_results", "0026_auto_20170130_1541")]

    operations = [
        migrations.AlterField(
            model_name="councilelection",
            name="council",
            field=models.ForeignKey(
                to="uk_results.Council", on_delete=models.CASCADE
            ),
        )
    ]
