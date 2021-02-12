from collections import defaultdict

from django.conf import settings

from elections.models import Election

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


def split_candidacies(election_data, memberships):
    # Group the candidates from memberships of a post into current and
    # past elections. To save queries, memberships should have their
    # 'extra' objects loaded with prefetch_related, and the 'election'
    # property of those 'extra' objects should have been loaded with
    # select_related.
    current_candidadacies = set()
    past_candidadacies = set()
    for membership in memberships:
        if membership.ballot.election == election_data:
            current_candidadacies.add(membership)
        elif membership.ballot.election:
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
                "ec_id": candidacy.party.ec_id,
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
                    "ec_id": k,
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
       form as the first argument. This is a breaking change from using the
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
        if hasattr(self, "get_object"):
            kwargs["instance"] = self.object
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

        if hasattr(self, "get_object"):
            self.object = self.get_object()
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
            if fs_name not in kwargs:
                kwargs[fs_name] = fs
        return super().get_context_data(**kwargs)
