from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [("tasks", "0001_initial")]

    operations = [
        migrations.AlterModelOptions(
            name="persontask", options={"ordering": ["task_priority"]}
        ),
        migrations.AddField(
            model_name="persontask",
            name="found",
            field=models.BooleanField(default=False),
        ),
    ]
