from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [("candidates", "0016_migrate_data_to_extra_fields")]

    operations = [
        migrations.RemoveField(model_name="personextra", name="cv"),
        migrations.RemoveField(model_name="personextra", name="program"),
    ]
