from __future__ import unicode_literals

from collections import defaultdict

from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect

from elections.models import Election

from slugify import slugify

from ..models import (
    MembershipExtra, PartySet, SimplePopoloField, ExtraField
)


def get_field_groupings():
    personal = [
        'name',
        'family_name',
        'given_name',
        'additional_name',
        'honorific_prefix',
        'honorific_suffix',
        'patronymic_name',
        'sort_name',
        'email',
        'summary',
        'biography',
    ]

    demographic = [
        'gender',
        'birth_date',
        'death_date',
        'national_identity',
    ]

    return (personal, demographic)


def get_redirect_to_post(election, post):
    from ..election_specific import shorten_post_label
    short_post_label = shorten_post_label(post.label)
    return HttpResponseRedirect(
        reverse(
            'constituency',
            kwargs={
                'election': election,
                'post_id': post.extra.slug,
                'ignored_slug': slugify(short_post_label),
            }
        )
    )


def get_person_form_fields(context, form):
    context['extra_fields'] = []
    extra_fields = ExtraField.objects.all()
    for field in extra_fields:
        context['extra_fields'].append(
            form[field.key]
        )

    personal_fields, demographic_fields = get_field_groupings()
    context['personal_fields'] = []
    context['demographic_fields'] = []
    simple_fields = SimplePopoloField.objects.order_by('order').all()
    for field in simple_fields:
        if field.name in personal_fields:
            context['personal_fields'].append(
                form[field.name]
            )

        if field.name in demographic_fields:
            context['demographic_fields'].append(
                form[field.name]
            )

    context['constituencies_form_fields'] = \
        get_candidacy_fields_for_person_form(form)

    return context


def get_candidacy_fields_for_person_form(form):
    fields = []
    for election_data in form.elections_with_fields:
        if not election_data.current:
            continue

        # Only show elections that we know this person to be standing in
        standing_id = 'standing_' + election_data.slug
        if not form.initial[standing_id] == 'standing':
            continue

        cons_form_fields = {
            'election': election_data,
            'election_name': election_data.name,
            'standing': form[standing_id],
            'constituency': form['constituency_' + election_data.slug],
        }
        party_fields = []
        for ps in PartySet.objects.all():
            key_suffix = ps.slug + '_' + election_data.slug
            position_field = None
            try:
                if election_data.party_lists_in_use:
                    position_field = form['party_list_position_' + key_suffix]
                party_position_tuple = (
                    form['party_' + key_suffix],
                    position_field
                )
            # the new person form often is specific to one election so doesn't
            # have all the party sets
            except KeyError:
                continue
            party_fields.append(party_position_tuple)
        cons_form_fields['party_fields'] = party_fields
        fields.append(cons_form_fields)

    return fields


def get_party_people_for_election_from_memberships(
        election,
        party_id,
        memberships
):
    election_data = Election.objects.get_by_slug(election)
    memberships = memberships.select_related('extra', 'person').filter(
        role=election_data.candidate_membership_role,
        extra__election=election_data,
        on_behalf_of_id=party_id
    ).order_by('extra__party_list_position').all()

    people = []
    for membership in memberships.all():
        people.append((
            membership.extra.party_list_position, membership.person,
            membership.extra.elected
        ))

    return people

def split_candidacies(election_data, memberships):
    # Group the candidates from memberships of a post into current and
    # past elections. To save queries, memberships should have their
    # 'extra' objects loaded with prefetch_related, and the 'election'
    # property of those 'extra' objects should have been loaded with
    # select_related.
    current_candidadacies = set()
    past_candidadacies = set()
    for membership in memberships:
        try:
            membership_extra = membership.extra
        except MembershipExtra.DoesNotExist:
            continue
        if membership_extra.election == election_data:
            if not membership.role == election_data.candidate_membership_role:
                continue
            current_candidadacies.add(membership)
        elif membership_extra.election:
            past_candidadacies.add(membership)

    return current_candidadacies, past_candidadacies

def group_candidates_by_party(election_data, candidacies, party_list=True, max_people=None):
    """Take a list of candidacies and return the people grouped by party

    This returns a tuple of the party_list boolean and a list of
    parties-and-people.

    The the parties-and-people list is a list of tuples; each tuple
    has two elements, the first of which is a dictionary with the
    party's ID and name, while the second is a list of people in that
    party.  The list of people for each party is sorted by their last
    names.

    The order of the tuples in the parties-and-people list is
    determined by the party_list parameter.  When party_list is True,
    the groups of parties are ordered by their names.  Otherwise
    (where there is typically one candidate per party), the groups
    will be ordered by the last name of the first candidate for each
    party."""

    party_id_to_name = {}
    party_id_to_people = defaultdict(list)
    party_truncated = dict()
    for candidacy in candidacies:
        party = candidacy.on_behalf_of
        party_id_to_name[party.extra.slug] = party.name
        position = candidacy.extra.party_list_position
        party_id_to_people[party.extra.slug].append(
            (position, candidacy.person, candidacy.extra.elected)
        )
    for party_id, people_list in party_id_to_people.items():
        if election_data.party_lists_in_use:
            # sort by party list position
            people_list.sort(key=lambda p: ( p[0] is None, p[0] ))
            # only return the configured maximum number of people
            # for a party list
            if max_people and len(people_list) > max_people:
                party_truncated[party_id] = len(people_list)
                del people_list[max_people:]
        else:
            people_list.sort(key=lambda p: p[1].family_name)
    try:
        result = [
            (
                {
                    'id': k,
                    'name': party_id_to_name[k],
                    'max_count': max_people,
                    'total_count': party_truncated.get(k)
                },
                # throw away the party list position data we
                # were only using for sorting
                [(p[1], p[2]) for p in v]
            )
            for k, v in party_id_to_people.items()
        ]
    except KeyError as ke:
        raise Exception("Unknown party: {0}".format(ke))
    if party_list:
        result.sort(key=lambda t: t[0]['name'])
    else:
        result.sort(key=lambda t: t[1][0][0].family_name)
    return {
        'party_lists_in_use': party_list,
        'parties_and_people': result
    }
