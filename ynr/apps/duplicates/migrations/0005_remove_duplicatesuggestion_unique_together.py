from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("duplicates", "0004_alter_duplicatesuggestion_status"),
    ]

    operations = [
        migrations.AlterUniqueTogether(
            name="duplicatesuggestion",
            unique_together=set(),
        ),
    ]
