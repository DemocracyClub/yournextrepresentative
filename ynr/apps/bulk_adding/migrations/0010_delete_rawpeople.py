from django.db import migrations


def delete_rawpeople(apps, schema_editor):
    RawPeople = apps.get_model("bulk_adding", "RawPeople")
    RawPeople.objects.all().delete()


class Migration(migrations.Migration):
    dependencies = [
        (
            "bulk_adding",
            "0009_remove_rawpeople_aws_textract_parsed_data_and_more",
        ),
    ]

    operations = [
        migrations.RunPython(
            code=delete_rawpeople, reverse_code=migrations.RunPython.noop
        )
    ]
