from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("uk_results", "0004_councilelection_party_set"),
    ]

    operations = [
        migrations.AddField(
            model_name="councilelectionresultset",
            name="confirm_source",
            field=models.TextField(null=True),
        ),
        migrations.AddField(
            model_name="councilelectionresultset",
            name="confirmed_by",
            field=models.ForeignKey(
                to=settings.AUTH_USER_MODEL, null=True, on_delete=models.CASCADE
            ),
        ),
        migrations.AddField(
            model_name="councilelectionresultset",
            name="final_source",
            field=models.TextField(null=True),
        ),
        migrations.AddField(
            model_name="councilelectionresultset",
            name="is_final",
            field=models.BooleanField(default=False),
        ),
    ]
