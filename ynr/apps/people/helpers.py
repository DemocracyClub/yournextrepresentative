import re

from dateutil import parser
from django.conf import settings
from django.utils.translation import ugettext_lazy as _l
from django_date_extensions.fields import ApproximateDate

from candidates.models import (
    ExtraField,
    PersonExtraFieldValue,
    PartySet,
    raise_if_unsafe_to_delete,
)
from candidates.twitter_api import (
    update_twitter_user_id,
    TwitterAPITokenMissing,
)
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
        ("Jan", _l("Jan"), "January", _l("January")),
        ("Feb", _l("Feb"), "February", _l("February")),
        ("Mar", _l("Mar"), "March", _l("March")),
        ("Apr", _l("Apr"), "April", _l("April")),
        ("May", _l("May"), "May", _l("May")),
        ("Jun", _l("Jun"), "June", _l("June")),
        ("Jul", _l("Jul"), "July", _l("July")),
        ("Aug", _l("Aug"), "August", _l("August")),
        ("Sep", _l("Sep"), "Sept", "September", _l("September")),
        ("Oct", _l("Oct"), "October", _l("October")),
        ("Nov", _l("Nov"), "November", _l("November")),
        ("Dec", _l("Dec"), "December", _l("December")),
    ]

    PERTAIN = ["of", _l("of")]


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
    for extra_field in ExtraField.objects.all():
        if extra_field.key in form_data:
            PersonExtraFieldValue.objects.update_or_create(
                person=person,
                field=extra_field,
                defaults={"value": form_data[extra_field.key]},
            )
    person.save()
    try:
        update_twitter_user_id(person)
    except TwitterAPITokenMissing:
        pass
    for election_data in form.elections_with_fields:
        # Interpret the form data relating to this election:
        post_id = form_data.get("constituency_" + election_data.slug)
        standing = form_data.pop("standing_" + election_data.slug, "standing")
        if post_id:
            party_set = PartySet.objects.get(post__slug=post_id)
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
            post = Post.objects.get(slug=post_id)
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
        post_election__election=election_data,
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
            post_election=election_data.postextraelection_set.get(post=post),
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
        post_election__election=election_data,
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
        post_election__election=election_data,
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
