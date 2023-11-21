from django.db import migrations


def mark_uncontested_winners(apps, schema_editor):
    """
    If the election is uncontested mark all candidates as elected
    """
    Ballot = apps.get_model("candidates", "Ballot")
    locked_ballots = Ballot.objects.filter(candidates_locked=True)
    uncontested_ballots = []
    for ballot in locked_ballots:
        if ballot.winner_count >= ballot.membership_set.count():
            uncontested_ballots.append(ballot)
            ballot.membership_set.update(elected=True)


class Migration(migrations.Migration):
    dependencies = [
        ("people", "0044_populate_biography_timestamp"),
    ]

    operations = [
        migrations.RunPython(
            code=mark_uncontested_winners,
            reverse_code=migrations.RunPython.noop,
        )
    ]
