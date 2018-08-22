from django.db import migrations, models


def create_tmp_ballot_paper_id_from_pee(apps, schema_editor):
    PostExtraElection = apps.get_model("candidates", "PostExtraElection")
    for pee in PostExtraElection.objects.all():
        pee.ballot_paper_id = "tmp_{}.{}".format(
            pee.election.slug, pee.postextra.slug
        )
        pee.save()


def do_nothing(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [("candidates", "0038_postextraelection_ballot_paper_id")]

    operations = [
        migrations.RunPython(create_tmp_ballot_paper_id_from_pee, do_nothing),
        migrations.AlterField(
            model_name="postextraelection",
            name="ballot_paper_id",
            field=models.CharField(unique=True, max_length=255, blank=True),
        ),
    ]
