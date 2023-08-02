from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [("candidates", "0011_migrate_loggedaction_person")]

    operations = [
        migrations.RemoveField(
            model_name="loggedaction", name="popit_person_id"
        )
    ]
