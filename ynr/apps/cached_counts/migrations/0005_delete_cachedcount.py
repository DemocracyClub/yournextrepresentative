from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [("cached_counts", "0004_constituency_to_post")]

    operations = [migrations.DeleteModel(name="CachedCount")]
