from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("uk_results", "0012_auto_20160427_1339"),
    ]

    operations = [
        migrations.AddField(
            model_name="resultset",
            name="final_source",
            field=models.TextField(null=True),
        ),
        migrations.AddField(
            model_name="resultset",
            name="is_final",
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name="resultset",
            name="review_source",
            field=models.TextField(null=True),
        ),
        migrations.AddField(
            model_name="resultset",
            name="review_status",
            field=models.CharField(
                blank=True,
                max_length=100,
                choices=[
                    (b"unconfirmed", b"Unconfirmed"),
                    (b"confirmed", b"Confirmed"),
                    (b"rejected", b"Rejected"),
                ],
            ),
        ),
        migrations.AddField(
            model_name="resultset",
            name="reviewed_by",
            field=models.ForeignKey(
                to=settings.AUTH_USER_MODEL, null=True, on_delete=models.CASCADE
            ),
        ),
        migrations.AlterField(
            model_name="councilelectionresultset",
            name="reviewed_by",
            field=models.ForeignKey(
                to=settings.AUTH_USER_MODEL, null=True, on_delete=models.CASCADE
            ),
        ),
    ]
