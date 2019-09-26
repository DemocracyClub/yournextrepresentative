from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("candidates", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="UserTermsAgreement",
            fields=[
                (
                    "id",
                    models.AutoField(
                        verbose_name="ID",
                        serialize=False,
                        auto_created=True,
                        primary_key=True,
                    ),
                ),
                ("assigned_to_dc", models.BooleanField(default=False)),
                (
                    "user",
                    models.OneToOneField(
                        related_name="terms_agreement",
                        to=settings.AUTH_USER_MODEL,
                        on_delete=models.CASCADE,
                    ),
                ),
            ],
            options={},
            bases=(models.Model,),
        )
    ]
