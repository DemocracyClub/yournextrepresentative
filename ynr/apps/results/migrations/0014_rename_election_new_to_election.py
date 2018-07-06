from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('results', '0013_remove_old_fields'),
    ]

    operations = [
        migrations.RenameField(
            model_name='resultevent',
            old_name='election_new',
            new_name='election',
        ),
    ]
