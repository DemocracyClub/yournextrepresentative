from django.db import migrations


def create_user_terms_agreements(apps, schema_editor):
    User = apps.get_model("auth", "User")
    UserTermsAgreement = apps.get_model("candidates", "UserTermsAgreement")
    for u in User.objects.all():
        UserTermsAgreement.objects.get_or_create(user=u)


class Migration(migrations.Migration):

    dependencies = [("candidates", "0002_usertermsagreement")]

    operations = [migrations.RunPython(create_user_terms_agreements)]
