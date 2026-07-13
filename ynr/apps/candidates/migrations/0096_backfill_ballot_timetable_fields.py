from django.db import migrations
from uk_election_timetables.calendars import Country
from uk_election_timetables.election_ids import (
    InvalidElectionIdError,
    from_election_id,
)

country_map = {
    "WLS": Country.WALES,
    "ENG": Country.ENGLAND,
    "NIR": Country.NORTHERN_IRELAND,
    "SCT": Country.SCOTLAND,
}


def backfill_timetable_fields(apps, schema_editor):
    Ballot = apps.get_model("candidates", "Ballot")

    qs = (
        Ballot.objects.using(schema_editor.connection.alias)
        # We don't have logic for computing timetable for
        # EU Parliament elections but some do exist in the DB
        # from back in the day
        .exclude(ballot_paper_id__startswith="europarl.")
    )
    ballots_to_update = []

    for ballot in qs.iterator():
        try:
            timetable = from_election_id(
                ballot.ballot_paper_id,
                country=country_map[ballot.post.territory_code],
            )
        except InvalidElectionIdError:
            # Some really old elections in YNR don't have a EE ballot ID
            continue

        ballot.close_of_nominations = timetable.close_of_nominations
        ballot.sopn_publish_deadline = timetable.sopn_publish_deadline
        ballots_to_update.append(ballot)

    batch_size = 2000
    for i in range(0, len(ballots_to_update), batch_size):
        qs.bulk_update(
            ballots_to_update[i : i + batch_size],
            ["close_of_nominations", "sopn_publish_deadline"],
        )


def clear_timetable_fields(apps, schema_editor):
    Ballot = apps.get_model("candidates", "Ballot")
    Ballot.objects.using(schema_editor.connection.alias).update(
        close_of_nominations=None,
        sopn_publish_deadline=None,
    )


class Migration(migrations.Migration):
    dependencies = [
        ("candidates", "0095_ballot_timetable_fields"),
    ]

    operations = [
        migrations.RunPython(backfill_timetable_fields, clear_timetable_fields)
    ]
