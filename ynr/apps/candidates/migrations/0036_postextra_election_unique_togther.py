from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('candidates', '0035_remove_postextra_candidates_locked'),
    ]

    operations = [
        migrations.AlterUniqueTogether(
            name='postextraelection',
            unique_together={('election', 'postextra')},
        ),
    ]
