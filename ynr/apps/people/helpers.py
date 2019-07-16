import re

from dateutil import parser
from django.conf import settings
from django_date_extensions.fields import ApproximateDate

from candidates.models import PartySet, raise_if_unsafe_to_delete
from candidates.twitter_api import get_twitter_user_id, TwitterAPITokenMissing
from popolo.models import Post, Membership
from parties.models import Party


def parse_approximate_date(s):
    """Take any reasonable date string, and return an ApproximateDate for it

    >>> ad = parse_approximate_date('2014-02-17')
    >>> type(ad)
    <class 'django_date_extensions.fields.ApproximateDate'>
    >>> ad
    2014-02-17
    >>> parse_approximate_date('2014-02')
    2014-02-00
    >>> parse_approximate_date('2014')
    2014-00-00
    >>> parse_approximate_date('future')
    future
    """

    for regexp in [
        r"^(\d{4})-(\d{2})-(\d{2})$",
        r"^(\d{4})-(\d{2})$",
        r"^(\d{4})$",
    ]:
        m = re.search(regexp, s)
        if m:
            return ApproximateDate(*(int(g, 10) for g in m.groups()))
    if s == "future":
        return ApproximateDate(future=True)
    if s:
        dt = parser.parse(
            s,
            parserinfo=localparserinfo(),
            dayfirst=settings.DD_MM_DATE_FORMAT_PREFERRED,
        )
        return ApproximateDate(dt.year, dt.month, dt.day)
    raise ValueError("Couldn't parse '{}' as an ApproximateDate".format(s))


class localparserinfo(parser.parserinfo):
    MONTHS = [
        ("Jan", "Jan", "January", "January"),
        ("Feb", "Feb", "February", "February"),
        ("Mar", "Mar", "March", "March"),
        ("Apr", "Apr", "April", "April"),
        ("May", "May", "May", "May"),
        ("Jun", "Jun", "June", "June"),
        ("Jul", "Jul", "July", "July"),
        ("Aug", "Aug", "August", "August"),
        ("Sep", "Sep", "Sept", "September", "September"),
        ("Oct", "Oct", "October", "October"),
        ("Nov", "Nov", "November", "November"),
        ("Dec", "Dec", "December", "December"),
    ]

    PERTAIN = ["of", "of"]


def update_person_from_form(person, form):
    form_data = form.cleaned_data.copy()
    # The date is returned as a datetime.date, so if that's set, turn
    # it into a string:
    birth_date_date = form_data["birth_date"]
    if birth_date_date:
        form_data["birth_date"] = repr(birth_date_date).replace("-00-00", "")
    else:
        form_data["birth_date"] = ""
    for field in settings.SIMPLE_POPOLO_FIELDS:
        setattr(person, field.name, form_data[field.name])

    person.favourite_biscuit = form_data["favourite_biscuit"]

    person.save()

    for election_data in form.elections_with_fields:
        # Interpret the form data relating to this election:
        post_id = form_data.get("constituency_" + election_data.slug)
        standing = form_data.pop("standing_" + election_data.slug, "standing")
        if post_id:
            post = Post.objects.get(
                slug=post_id, ballot__election=election_data
            )
            party_set = PartySet.objects.get(post=post)
            party_key = (
                "party_" + party_set.slug.upper() + "_" + election_data.slug
            )
            position_key = (
                "party_list_position_"
                + party_set.slug.upper()
                + "_"
                + election_data.slug
            )
            party = Party.objects.get(ec_id=form_data[party_key])
            party_list_position = form_data.get(position_key) or None

        else:
            party = None
            party_list_position = None
            post = None
        # Now update the candidacies and not_standing based on those values:
        if standing == "standing":
            mark_as_standing(
                person, election_data, post, party, party_list_position
            )
        elif standing == "not-standing":
            mark_as_not_standing(person, election_data, post)
        else:
            mark_as_unsure_if_standing(person, election_data, post)


def mark_as_standing(person, election_data, post, party, party_list_position):
    # First, if the person is marked as "not standing" in that
    # election, remove that record:
    person.not_standing.remove(election_data)
    membership_ids_to_remove = set()
    membership = None
    # This person might already be marked as standing for this
    # post. In that case, we need to make sure we preserve that
    # existing membership, since there may be metadata attached to it
    # (such as the extra.elected property or CandidateResult records)
    # which would be lost if we deleted and recreated the membership.
    # Go through the person's existing candidacies for this election:
    for existing_membership in Membership.objects.filter(
        ballot__election=election_data,
        role=election_data.candidate_membership_role,
        person=person,
    ):
        if existing_membership.post == post:
            membership = existing_membership
        else:
            membership_ids_to_remove.add(existing_membership.id)
    # If there was no existing membership, we need to create one:
    if not membership:
        membership = Membership.objects.create(
            post=post,
            person=person,
            role=election_data.candidate_membership_role,
            ballot=election_data.ballot_set.get(post=post),
        )
    # Update the party list position in case it's changed:
    membership.party_list_position = party_list_position
    membership.save()
    # Update the party, in case it's changed:
    membership.party = party
    membership.save()
    # Now remove any memberships that shouldn't now be there:
    for membership_to_remove in Membership.objects.filter(
        pk__in=membership_ids_to_remove
    ):
        raise_if_unsafe_to_delete(membership_to_remove)
        membership_to_remove.delete()


def mark_as_not_standing(person, election_data, post):
    # Remove any existing candidacy:
    for membership in Membership.objects.filter(
        ballot__election=election_data,
        role=election_data.candidate_membership_role,
        person=person,
        # n.b. we are planning to make "not standing" post
        # specific in the future, in which case we would also want
        # this line:
        # post__slug=post_slug,
    ):
        raise_if_unsafe_to_delete(membership)
        membership.delete()
    from candidates.models.constraints import check_no_candidancy_for_election

    check_no_candidancy_for_election(person, election_data)
    person.not_standing.add(election_data)


def mark_as_unsure_if_standing(person, election_data, post):
    # Remove any existing candidacy:
    for membership in Membership.objects.filter(
        ballot__election=election_data,
        role=election_data.candidate_membership_role,
        person=person,
    ):
        raise_if_unsafe_to_delete(membership)
        membership.delete()
    # Now remove any entry that indicates that they're standing in
    # this election:
    person.not_standing.remove(election_data)


def squash_whitespace(s):
    # Take any run of more than one whitespace character, and replace
    # it either with a newline (if that replaced text contained a
    # newline) or a space (otherwise).
    return re.sub(
        r"(?ims)\s+", lambda m: "\n" if "\n" in m.group(0) else " ", s
    )


def clean_twitter_username(username):
    # Remove any URL bits around it:
    username = username.strip()
    m = re.search(r"^.*twitter.com/(\w+)", username)
    if m:
        username = m.group(1)
    # If there's a leading '@', strip that off:
    username = re.sub(r"^@", "", username)
    if not re.search(r"^\w*$", username):
        message = "The Twitter username must only consist of alphanumeric characters or underscore"
        raise ValueError(message)
    if username:
        try:
            user_id = get_twitter_user_id(username)
            if not user_id:
                message = "The Twitter account {screen_name} doesn't exist"
                raise ValueError(message.format(screen_name=username))
        except TwitterAPITokenMissing:
            # If there's no API token, we can't check the screen name,
            # but don't fail validation because the site owners
            # haven't set that up.
            return username
    return username


def clean_wikidata_id(identifier):
    identifier = identifier.strip().lower()
    m = re.search(r"^.*wikidata.org/(wiki|entity)/(\w+)", identifier)
    if m:
        identifier = m.group(2)
    identifier = identifier.upper()
    if not re.match("Q[\d]+", identifier):
        raise ValueError("Wikidata ID be a 'Q12345' type identifier")
    return identifier
