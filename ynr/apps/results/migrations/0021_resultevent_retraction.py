from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('results', '0020_remove_resultevent_proxy_image_url_template'),
    ]

    operations = [
        migrations.AddField(
            model_name='resultevent',
            name='retraction',
            field=models.BooleanField(default=False),
        ),
    ]
