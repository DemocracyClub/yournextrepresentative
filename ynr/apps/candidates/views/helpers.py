from collections import defaultdict

from django.conf import settings
from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect

from elections.models import Election

from slugify import slugify

from ..models import PartySet


def get_field_groupings():
    personal = [
        "name",
        "family_name",
        "given_name",
        "additional_name",
        "honorific_prefix",
        "honorific_suffix",
        "patronymic_name",
        "sort_name",
        "email",
        "summary",
        "biography",
    ]

    demographic = ["gender", "birth_date", "death_date", "national_identity"]

    return (personal, demographic)


def get_redirect_to_post(election, post):
    pee = election.postextraelection_set.get(post=post)
    return HttpResponseRedirect(pee.get_absolute_url())


def get_person_form_fields(context, form):
    context["extra_fields"] = []

    personal_fields, demographic_fields = get_field_groupings()
    context["personal_fields"] = []
    context["demographic_fields"] = []
    simple_fields = settings.SIMPLE_POPOLO_FIELDS
    for field in simple_fields:
        if field.name in personal_fields:
            context["personal_fields"].append(form[field.name])

        if field.name in demographic_fields:
            context["demographic_fields"].append(form[field.name])

    context[
        "constituencies_form_fields"
    ] = get_candidacy_fields_for_person_form(form)

    return context


def get_candidacy_fields_for_person_form(form):
    fields = []
    for election_data in form.elections_with_fields:
        if not election_data.current:
            continue

        # Only show elections that we know this person to be standing in
        standing_id = "standing_" + election_data.slug
        if not form.initial[standing_id] == "standing":
            continue

        cons_form_fields = {
            "election": election_data,
            "election_name": election_data.name,
            "standing": form[standing_id],
            "constituency": form["constituency_" + election_data.slug],
        }
        party_fields = []
        for ps in PartySet.objects.all():
            key_suffix = ps.slug.upper() + "_" + election_data.slug
            position_field = None
            try:
                if election_data.party_lists_in_use:
                    position_field = form["party_list_position_" + key_suffix]
                party_position_tuple = (
                    form["party_" + key_suffix],
                    position_field,
                )
            # the new person form often is specific to one election so doesn't
            # have all the party sets
            except KeyError:
                continue
            party_fields.append(party_position_tuple)
        cons_form_fields["party_fields"] = party_fields
        fields.append(cons_form_fields)

    return fields


def get_party_people_for_election_from_memberships(
    election, party_id, memberships
):
    election_data = Election.objects.get_by_slug(election)
    memberships = (
        memberships.select_related("person")
        .filter(
            role=election_data.candidate_membership_role,
            post_election__election=election_data,
            party__ec_id=party_id,
        )
        .order_by("party_list_position")
        .all()
    )

    people = []
    for membership in memberships.all():
        people.append(
            (
                membership.party_list_position,
                membership.person,
                membership.elected,
            )
        )

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
        if membership.post_election.election == election_data:
            current_candidadacies.add(membership)
        elif membership.post_election.election:
            past_candidadacies.add(membership)

    return current_candidadacies, past_candidadacies


def split_by_elected(election_data, memberships):
    elected_candidates = set()
    unelected_candidates = set()
    for membership in memberships:
        if membership.elected:
            elected_candidates.add(membership)
            if not settings.HOIST_ELECTED_CANDIDATES:
                unelected_candidates.add(membership)
        else:
            unelected_candidates.add(membership)

    return elected_candidates, unelected_candidates


def order_candidates_by_name_no_grouping(election_data, candidacies):
    result = [
        (
            {
                "id": candidacy.party.ec_id,
                "legacy_slug": candidacy.party.legacy_slug,
                "name": candidacy.party.name,
                "max_count": 0,
                "truncated": False,
                "total_count": 1,
            },
            [(None, candidacy.person, candidacy.elected)],
        )
        for candidacy in candidacies
    ]
    result.sort(key=lambda t: t[1][0][1].name.split()[-1])
    return {"party_lists_in_use": False, "parties_and_people": result}


def group_candidates_by_party(election_data, candidacies, show_all=False):
    """Take a list of candidacies and return the people grouped by party

    This returns a tuple of the party_list boolean and a list of
    parties-and-people.

    The parties-and-people list is a list of tuples; each tuple has
    two elements, the first of which is a dictionary with party data
    (e.g. its ID and name), while the second is a list of people in
    that party.  The list of people for each party is sorted by their
    last names.

    If party_list is True, the parties are sorted alphabetically and
    the candidates within each party group are sorted by their last
    name.

    Otherwise, if party_list is False, no grouping by party is done -
    the candidates are sorted by their last name.  (That means that if
    there's more than one candidate for a party and party_list is
    False, that party will once in the list for each candidate.)
    """

    party_list = election_data.party_lists_in_use
    if show_all:
        max_people = None
    else:
        max_people = election_data.default_party_list_members_to_show

    if not party_list:
        return order_candidates_by_name_no_grouping(election_data, candidacies)

    party_id_to_name = {}
    party_id_to_legacy_slug = {}
    party_id_to_people = defaultdict(list)
    party_truncated = dict()
    party_total = dict()
    for candidacy in candidacies:
        party = candidacy.party
        party_id_to_name[party.ec_id] = party.name
        party_id_to_legacy_slug[party.ec_id] = party.legacy_slug
        position = candidacy.party_list_position
        party_id_to_people[party.ec_id].append(
            (position, candidacy.person, candidacy.elected)
        )
    for party_id, people_list in party_id_to_people.items():
        truncated = False
        total_count = len(people_list)
        # sort by party list position
        people_list.sort(key=lambda p: (p[0] is None, p[0]))
        # only return the configured maximum number of people
        # for a party list
        if max_people and len(people_list) > max_people:
            truncated = True
            del people_list[max_people:]
        party_truncated[party_id] = truncated
        party_total[party_id] = total_count
    try:
        result = [
            (
                {
                    "id": k,
                    "name": party_id_to_name[k],
                    "legacy_slug": party_id_to_legacy_slug[k],
                    "max_count": max_people,
                    "truncated": party_truncated[k],
                    "total_count": party_total[k],
                },
                v,
            )
            for k, v in party_id_to_people.items()
        ]
    except KeyError as ke:
        raise Exception("Unknown party: {}".format(ke))
    if party_list:
        result.sort(key=lambda t: t[0]["name"])
    else:
        result.sort(key=lambda t: t[1][0][1].name.split()[-1])
    return {"party_lists_in_use": party_list, "parties_and_people": result}


class ProcessInlineFormsMixin:
    """
    A mixin class for `FormView` that handles inline formsets.


    To use:
    1. add `ProcessInlineFormsMixin` to your FormView class
    2. set `inline_formset_classes` to a dict containing the name of the
       inline formset you want in the template context and the inline formset
       class. You can also override `get_inline_formsets` with a method that
       returns a dict of the same structure.
    3. If your inline formsets require any kwargs when instantiated,
       override the `get_inline_formset_kwargs` method. This method will be
       called with the formset name (the key of the `inline_formset_classes`)
       and should return a dict with the kwargs for the form class.

    How it works:
    1. Each inline formset class in inline_formset_classes is instantiated with
       the kwargs returned by `get_inline_formset_kwargs`. They are bound to
       self.request.POST if the request method is POST.
    2. Each of these classes is added to the request context under the key used
       in`inline_formset_classes`.
    3. On POST to the view, `is_valid` is called on each inline formset, as well
       as the main `form` object.
    4. If all forms are valid, self.form_valid is called, with a dict of each
       form as the first arguement. This is a breaking change from using the
       standard FormView that expects a single Form class.
    5. if not, self.form_invalid is called with a dict of all forms.

    """

    inline_formset_classes = {}

    def get_inline_formsets(self):
        return self.inline_formset_classes

    def get_inline_formset_kwargs(self, formset_name):
        return {}

    def get_inline_formset(self, formset_name):
        formset = self.get_inline_formsets()[formset_name]
        kwargs = self.get_inline_formset_kwargs(formset_name)
        if self.request.method == "POST":
            return formset(self.request.POST, self.request.FILES, **kwargs)
        else:
            return formset(**kwargs)

    def get_all_initialized_inline_formsets(self):
        return {
            fs_name: self.get_inline_formset(fs_name)
            for fs_name in self.get_inline_formsets().keys()
        }

    def post(self, request, *args, **kwargs):
        """
        Handles POST requests, instantiating a form instance with the passed
        POST variables and then checked for validity.

        Copied from Django's `ProcessFormView`
        """
        form = self.get_form()
        all_forms = self.get_all_initialized_inline_formsets()
        all_forms["form"] = form
        all_valid = all([f.is_valid() for f in all_forms.values()])

        if all_valid:
            return self.form_valid(all_forms)
        else:
            return self.form_invalid(all_forms)

    def form_invalid(self, all_forms):
        """
        If the form is invalid, re-render the context data with the
        data-filled form and errors.
        """
        return self.render_to_response(self.get_context_data(**all_forms))

    def get_context_data(self, **kwargs):
        """
        Insert the formsets into the context dict.
        """
        for fs_name, fs in self.get_all_initialized_inline_formsets().items():
            if not fs_name in kwargs:
                kwargs[fs_name] = fs
        return super().get_context_data(**kwargs)


def get_max_winners(post_election):
    """
    If we know the winner count for this ballot, return it, otherwise return 0

    This is because the source of truth for winners is
    elections.democracyclub.org.uk. If it's not set there (and therefore at
    import time) then there is a high chance that we don't know the winner_count
    at all yet.

    Setting the winner_count to 0 will prevent things like setting winners or
    showing winners.

    TODO: move this on to the PostExtraElection model, or set it as a default
          in the database, TBD, see comment in
          https://github.com/DemocracyClub/yournextrepresentative/pull/621#issuecomment-417252565

    """
    if post_election.winner_count:

        return post_election.winner_count

    return 0
