from django.db import migrations


def get_candidate_rank(apps, schema_editor):
    """Only update the rank for the candidate results in a
    given resultset. It's possible that a resultset exists
    without any candidate results, so we need to check for
    that first.
    """
    candidate_result = apps.get_model("uk_results", "CandidateResult")
    resultsets = apps.get_model("uk_results", "ResultSet")
    for resultset in resultsets.objects.all():
        candidate_results = candidate_result.objects.filter(
            result_set=resultset
        ).order_by("-num_ballots")

        if candidate_results.exists():
            for i, cr in enumerate(candidate_results):
                if cr.rank is None:
                    cr.rank = i + 1
                    cr.save()
                else:
                    pass
        else:
            pass


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
