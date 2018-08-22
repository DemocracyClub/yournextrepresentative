from contextlib import contextmanager
import re

from django.core.exceptions import ObjectDoesNotExist

from popolo.models import Post

from uk_results.models import CandidateResult


def shorten_post_label(post_label):
    result = re.sub(r"^Member of Parliament for ", "", post_label)
    result = re.sub(r"^Member of the Scottish Parliament for ", "", result)
    result = re.sub(r"^Assembly Member for ", "", result)
    result = re.sub(r"^Member of the Legislative Assembly for ", "", result)
    return result


EXTRA_CSV_ROW_FIELDS = [
    "gss_code",
    "parlparse_id",
    "theyworkforyou_url",
    "party_ec_id",
    "favourite_biscuits",
]


def get_extra_csv_values(person, election, post):
    gss_code = ""
    parlparse_id = ""
    theyworkforyou_url = ""
    party_ec_id = ""
    for i in person.identifiers.all():
        if i.scheme == "uk.org.publicwhip":
            parlparse_id = i.identifier
            m = re.search(r"^uk.org.publicwhip/person/(\d+)$", parlparse_id)
            if not m:
                message = "Malformed parlparse ID found {0}"
                raise Exception(message.format(parlparse_id))
            theyworkforyou_url = "http://www.theyworkforyou.com/mp/{}".format(
                m.group(1)
            )
    for m in person.memberships.all():
        if m.post_election.election != election:
            continue
        expected_role = m.post_election.election.candidate_membership_role
        if expected_role != m.role:
            continue
        if m.post != post:
            continue
        # Now m / m_extra should be the candidacy membership:
        for i in m.on_behalf_of.identifiers.all():
            if i.scheme == "electoral-commission":
                party_ec_id = i.identifier
        # TODO Add identifiers here
        break
    favourite_biscuits = ""
    for efv in person.extra_field_values.all():
        if efv.field.key == "favourite_biscuits":
            favourite_biscuits = efv.value
    return {
        "gss_code": gss_code,
        "parlparse_id": parlparse_id,
        "theyworkforyou_url": theyworkforyou_url,
        "party_ec_id": party_ec_id,
        "favourite_biscuits": favourite_biscuits,
    }


def is_valid_postcode(postcode):
    outcode_pattern = "[A-PR-UWYZ]([0-9]{1,2}|([A-HIK-Y][0-9](|[0-9]|[ABEHMNPRVWXY]))|[0-9][A-HJKSTUW])"
    incode_pattern = "[0-9][ABD-HJLNP-UW-Z]{2}"
    postcode_regex = re.compile(
        r"^(GIR 0AA|{} {})$".format(outcode_pattern, incode_pattern)
    )
    space_regex = re.compile(r" *(%s)$" % incode_pattern)

    postcode = postcode.upper().strip()

    postcode = space_regex.sub(r" \1", postcode)
    if not postcode_regex.search(postcode):
        return False
    return True


@contextmanager
def additional_merge_actions(primary_person, secondary_person):
    # Before merging, save any CandidateResult objects that were
    # attached to either person's memberships. (All the memberships
    # are recreated as part when merging.)
    saved_crs = [
        (
            cr,
            {
                "post": cr.membership.post,
                "role": cr.membership.role,
                "post_election__election": cr.membership.post_election.election,
                "organization": cr.membership.organization,
                "on_behalf_of": cr.membership.on_behalf_of,
            },
        )
        for cr in CandidateResult.objects.filter(
            membership__person__in=(primary_person, secondary_person)
        )
    ]
    # Then do the merge as normal:
    yield
    # Now reassociate any saved CandidateResult objects with the
    # appropriate membership on the primary person:
    for saved_cr, membership_attrs in saved_crs:
        primary_membership = primary_person.memberships.get(**membership_attrs)
        saved_cr.membership = primary_membership
        saved_cr.save()
