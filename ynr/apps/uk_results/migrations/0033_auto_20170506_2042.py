from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('uk_results', '0032_rename_postresult_to_postelectionresult'),
    ]

    operations = [
        migrations.RenameField(
            model_name='resultset',
            old_name='post_result',
            new_name='post_election_result',
        ),
    ]
