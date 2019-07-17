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


def get_extra_csv_values(person, election, post):
    gss_code = ""
    parlparse_id = ""
    theyworkforyou_url = ""
    party_ec_id = ""
    cancelled_poll = ""

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
        if m.ballot.election != election:
            continue
        expected_role = m.ballot.election.candidate_membership_role
        if expected_role != m.role:
            continue
        if m.post != post:
            continue
        # Now m / m_extra should be the candidacy membership:
        party_ec_id = m.party.ec_id
        cancelled_poll = m.ballot.cancelled
        # TODO Add ballot id here
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
        "cancelled_poll": cancelled_poll,
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
