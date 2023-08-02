from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [("uk_results", "0025_minus-1-to-null-on-num-fields")]

    operations = [
        migrations.AlterModelOptions(
            name="councilelectionresultset",
            options={"get_latest_by": "modified"},
        ),
        migrations.AlterModelOptions(
            name="resultset", options={"get_latest_by": "modified"}
        ),
    ]
