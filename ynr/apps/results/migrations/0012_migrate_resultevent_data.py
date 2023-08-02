from django.db import migrations


def migrate_remaining_fields_to_popolo_models(apps, schema_editor):
    ResultEvent = apps.get_model("results", "ResultEvent")
    Organization = apps.get_model("popolo", "Organization")
    Post = apps.get_model("popolo", "Post")
    Election = apps.get_model("elections", "Election")
    for re in ResultEvent.objects.all():
        # Get the post, if possible (some have been deleted), and the
        # election based on the existing text-based fields:
        if re.election == "2015":
            election_name = "2015 General Election"
        else:
            election_name = re.election
        post = Post.objects.filter(extra__slug=re.post_id).first()
        if post:
            election = post.extra.elections.filter(name=election_name).first()
            if not election:
                election = post.extra.elections.get(
                    name=election_name, election_date__year=re.created.year
                )
        else:
            election = Election.objects.filter(
                name=re.election, election_date__lte=re.created
            ).first()
        re.election_new = election
        re.post_new = post
        # Now get the party of the winner:
        re.winner_party_new = Organization.objects.get(
            extra__slug=re.winner_party_id
        )
        re.save()


class Migration(migrations.Migration):
    dependencies = [("results", "0011_resultevent_post_new")]

    operations = [
        migrations.RunPython(migrate_remaining_fields_to_popolo_models)
    ]
