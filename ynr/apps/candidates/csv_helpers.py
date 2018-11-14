from collections import defaultdict

from compat import BufferDictWriter
from django.conf import settings

from popolo.models import Membership
from candidates.models import PersonRedirect


def list_to_csv(membership_list):

    csv_fields = settings.CSV_ROW_FIELDS
    writer = BufferDictWriter(fieldnames=csv_fields)
    writer.writeheader()
    for row in membership_list:
        writer.writerow(row)
    return writer.output


def memberships_dicts_for_csv(election_slug=None, post_slug=None):
    redirects = PersonRedirect.all_redirects_dict()
    memberships = Membership.objects.joins_for_csv()
    if election_slug:
        memberships = memberships.filter(
            post_election__election__slug=election_slug
        )
    if post_slug:
        memberships = memberships.filter(post_election__post__slug=post_slug)

    memberships_by_election = defaultdict(list)
    elected_by_election = defaultdict(list)

    for membership in memberships:
        election_slug = membership.post_election.election.slug
        line = membership.dict_for_csv(redirects=redirects)
        memberships_by_election[election_slug].append(line)
        if membership.elected:
            elected_by_election[election_slug].append(line)

    return (memberships_by_election, elected_by_election)
