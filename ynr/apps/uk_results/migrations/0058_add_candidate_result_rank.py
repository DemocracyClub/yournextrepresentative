from django.db import migrations


def get_candidate_rank(apps, schema_editor):
    candidate_results = apps.get_model("uk_results", "CandidateResult")
    results = candidate_results.objects.filter(rank=None).order_by(
        "-num_ballots"
    )
    for index, result in enumerate(results):
        index = index + 1
        result.rank = index
        result.save()


class Migration(migrations.Migration):
    dependencies = [
        ("uk_results", "0057_candidateresult_rank"),
    ]

    operations = [
        migrations.RunPython(
            get_candidate_rank,
            migrations.RunPython.noop,
        ),
    ]
