from candidates.diffs import get_version_diffs
from dateutil.parser import parse
from django.db import migrations
from django.utils.timezone import make_aware


def populate_biography_last_updated_timestamp(apps, schema_editor):
    Person = apps.get_model("people", "Person")
    for person in Person.objects.all().exclude(biography=""):
        try:
            diffs = get_version_diffs(person.versions)
            if diffs:
                for diff in diffs:
                    if diff["data"].get("biography"):
                        person.biography_last_updated = make_aware(
                            parse(diff["timestamp"])
                        )
                        person.save()
                        break
            else:
                person.biography_last_updated = person.created
                person.save()
        except Exception as e:
            print(f"Error on {person.pk}: {e}")


class Migration(migrations.Migration):
    dependencies = [("people", "0043_person_biography_last_updated")]

    operations = [
        migrations.RunPython(
            populate_biography_last_updated_timestamp,
            migrations.RunPython.noop,
        )
    ]
