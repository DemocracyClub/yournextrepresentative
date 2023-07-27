from collections import defaultdict

from candidates.models import PersonRedirect
from django.conf import settings
from popolo.models import Membership
from utils.dict_io import BufferDictWriter


def list_to_csv(membership_list):

    csv_fields = settings.CSV_ROW_FIELDS
    writer = BufferDictWriter(fieldnames=csv_fields)
    writer.writeheader()
    for row in sorted(membership_list, key=lambda d: (d["election_date"])):
        writer.writerow(row)
    return writer.output


def sort_memberships(membership_list):
    return sorted(
        membership_list,
        key=lambda d: (d["election_date"], d["post_id"], d["id"]),
        reverse=True,
    )


def memberships_dicts_for_csv(election_slug=None, post_slug=None):
    redirects = PersonRedirect.all_redirects_dict()
    memberships = Membership.objects.for_csv()
    if election_slug:
        memberships = memberships.filter(ballot__election__slug=election_slug)
    if post_slug:
        memberships = memberships.filter(ballot__post__slug=post_slug)

    memberships_by_election = defaultdict(list)
    elected_by_election = defaultdict(list)

    # NB by using iterator this will ignore previous prefetch_related
    # calls see https://docs.djangoproject.com/en/4.0/ref/models/querysets/#iterator
    for membership in memberships.iterator(chunk_size=4000):
        election_slug = membership.ballot.election.slug
        line = membership.dict_for_csv(redirects=redirects)
        memberships_by_election[election_slug].append(line)
        if membership.elected:
            elected_by_election[election_slug].append(line)

    for election_slug, membership_list in memberships_by_election.items():
        sort_memberships(membership_list)
    for election_slug, membership_list in elected_by_election.items():
        sort_memberships(membership_list)

    return (memberships_by_election, elected_by_election)
