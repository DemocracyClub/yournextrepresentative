import re
from urllib.parse import quote

from auth_helpers.views import GroupRequiredMixin, user_in_group
from braces.views import LoginRequiredMixin
from candidates.models.db import ActionType
from django.conf import settings
from django.contrib import messages
from django.core.exceptions import PermissionDenied
from django.db import transaction
from django.http import (
    Http404,
    HttpResponsePermanentRedirect,
    HttpResponseRedirect,
)
from django.shortcuts import get_object_or_404, redirect
from django.template.loader import render_to_string
from django.urls import reverse, reverse_lazy
from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_control
from django.views.generic import FormView, TemplateView, UpdateView, View
from django.views.generic.detail import DetailView
from duplicates.forms import DuplicateSuggestionForm
from elections.mixins import ElectionMixin
from elections.models import Election
from elections.uk.forms import SelectBallotForm
from people.forms.forms import (
    NewPersonForm,
    PersonSplitForm,
    PersonSplitFormSet,
    UpdatePersonForm,
)
from people.forms.formsets import (
    PersonIdentifierFormsetFactory,
    PersonMembershipFormsetFactory,
)
from people.models import Person
from popolo.models import NotStandingValidationError

from ynr.apps.people.merging import InvalidMergeError, PersonMerger

from ..diffs import get_version_diffs
from ..models import (
    TRUSTED_TO_MERGE_GROUP_NAME,
    Ballot,
    LoggedAction,
    PersonRedirect,
)
from ..models.versions import revert_person_from_version_data
from .helpers import ProcessInlineFormsMixin
from .version_data import get_change_metadata, get_client_ip


def get_call_to_action_flash_message(person, new_person=False):
    """Get HTML for a flash message after a person has been created or updated"""
    return render_to_string(
        "candidates/_person_update_call_to_action.html",
        {
            "new_person": new_person,
            "person_url": reverse(
                "person-view", kwargs={"person_id": person.id}
            ),
            "person_edit_url": reverse(
                "person-update", kwargs={"person_id": person.id}
            ),
            "person_name": person.name,
            "needing_attention_url": reverse("attention_needed"),
            # We want to offer the option to add another candidate in
            # any of the elections that this candidate is standing in,
            # which means we'll need the "create person" URL and
            # election name for each of those elections:
            "create_for_election_options": [
                (
                    reverse(
                        "person-create",
                        kwargs={"ballot_paper_id": ballot.ballot_paper_id},
                    ),
                    ballot.post.label,
                )
                for ballot in Ballot.objects.filter(
                    membership__person=person, election__current=True
                )
                .select_related("post")
                .distinct()
                .order_by("ballot_paper_id")
            ],
        },
    )


SUGGESTION_FORM_ID = "suggestion"
MERGE_FORM_ID = "merge"


class PersonView(TemplateView):
    template_name = "candidates/person-view.html"

    @method_decorator(cache_control(max_age=(60 * 20)))
    def dispatch(self, *args, **kwargs):
        return super().dispatch(*args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        path = self.person.get_absolute_url()
        context["redirect_after_login"] = quote(path)
        context["canonical_url"] = self.person.wcivf_url()
        context["person"] = self.person
        context["other_names"] = self.person.other_names
        if not self.request.user.is_authenticated:
            context["other_names"] = context["other_names"].filter(
                needs_review=False
            )

        context["elections_to_list"] = Election.objects.filter(
            ballot__membership__person=self.person
        ).order_by("-election_date")

        context["last_candidacy"] = self.person.last_candidacy
        context["election_to_show"] = None
        context["has_current_elections"] = (
            context["elections_to_list"].current_or_future().exists()
        )

        context["person_edits_allowed"] = self.person.user_can_edit(
            self.request.user
        )
        context["SUGGESTION_FORM_ID"] = SUGGESTION_FORM_ID

        return context

    def get(self, request, *args, **kwargs):
        person_id = self.kwargs["person_id"]
        try:
            self.person = Person.objects.prefetch_related(
                "tmp_person_identifiers"
            ).get(pk=person_id)
        except Person.DoesNotExist:
            try:
                return self.get_person_redirect(person_id)
            except PersonRedirect.DoesNotExist:
                raise Http404(
                    "No person found with ID {person_id}".format(
                        person_id=person_id
                    )
                )
        return super().get(request, *args, **kwargs)

    def get_person_redirect(self, person_id):
        # If there's a PersonRedirect for this person ID, do the
        # redirect, otherwise process the GET request as usual.
        # try:
        new_person_id = PersonRedirect.objects.get(
            old_person_id=person_id
        ).new_person_id
        return HttpResponsePermanentRedirect(
            reverse("person-view", kwargs={"person_id": new_person_id})
        )


class RevertPersonView(LoginRequiredMixin, View):
    http_method_names = ["post"]

    def post(self, request, *args, **kwargs):
        version_id = self.request.POST["version_id"]
        person_id = self.kwargs["person_id"]
        source = self.request.POST["source"]

        with transaction.atomic():
            person = get_object_or_404(Person, id=person_id)
            versions = person.versions
            data_to_revert_to = None
            for version in versions:
                if version["version_id"] == version_id:
                    data_to_revert_to = version["data"]
                    break

            if not data_to_revert_to:
                message = "Couldn't find the version {0} of person {1}"
                raise Exception(message.format(version_id, person_id))

            change_metadata = get_change_metadata(self.request, source)

            # Update the person here...
            revert_person_from_version_data(person, data_to_revert_to)

            person.record_version(change_metadata)
            person.save()

            # Log that that action has taken place, and will be shown in
            # the recent changes, leaderboards, etc.
            LoggedAction.objects.create(
                user=self.request.user,
                person=person,
                action_type=ActionType.PERSON_REVERT,
                ip_address=get_client_ip(self.request),
                popit_person_new_version=change_metadata["version_id"],
                source=change_metadata["information_source"],
            )

        return HttpResponseRedirect(
            reverse("person-view", kwargs={"person_id": person_id})
        )


class MergePeopleMixin:
    def do_merge(self, primary_person, secondary_person):
        merger = PersonMerger(
            primary_person, secondary_person, request=self.request
        )

        return merger.merge(delete=True)


class DuplicatePersonView(LoginRequiredMixin, FormView, DetailView):
    """
    A view that allows a user to suggest a duplicate person. Users with merge
    permissions can merge directly rather than creating a DuplicateSuggestion
    """

    http_method_names = ["get", "post"]
    template_name = "duplicates/duplicate_suggestion.html"
    model = Person
    context_object_name = "person"
    pk_url_kwarg = "person_id"
    extra_context = {
        "SUGGESTION_FORM_ID": SUGGESTION_FORM_ID,
        "MERGE_FORM_ID": MERGE_FORM_ID,
    }
    form_class = DuplicateSuggestionForm

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["person"] = self.object
        kwargs["user"] = self.request.user
        if self.request.method == "GET":
            kwargs["data"] = self.request.GET
        return kwargs

    def get(self, request, *args, **kwargs):
        self.object = self.get_object()
        context = self.get_context_data()
        form = context["form"]
        if not form.is_valid():
            context["errors"] = True

        return self.render_to_response(context)

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        return super().post(request, *args, **kwargs)

    def form_valid(self, form):
        """
        Create the suggestestion, add a message, and redirect to
        person profile they came from
        """
        with transaction.atomic():
            suggestion = form.save()
            LoggedAction.objects.create(
                user=self.request.user,
                person=self.object,
                action_type=ActionType.DUPLICATE_SUGGEST,
                ip_address=get_client_ip(self.request),
                source="duplicate person suggested",
            )
            msg = f"Thanks, your duplicate suggestion for ID:{suggestion.person.pk} and ID:{suggestion.other_person.pk} was created."
            messages.add_message(
                request=self.request,
                level=messages.SUCCESS,
                message=msg,
                extra_tags="safe do-something-else",
            )
            return HttpResponseRedirect(self.object.get_absolute_url())

    def get_context_data(self, **kwargs):
        """
        Check whether user can merge directly, which is used in the
        template to determine whether merge button is displayed
        """
        context = super().get_context_data(**kwargs)
        context["user_can_merge"] = user_in_group(
            self.request.user, TRUSTED_TO_MERGE_GROUP_NAME
        )
        return context


class MergePeopleView(GroupRequiredMixin, TemplateView, MergePeopleMixin):
    http_method_names = ["get", "post"]
    required_group_name = TRUSTED_TO_MERGE_GROUP_NAME
    template_name = "candidates/generic-merge-error.html"

    def validate(self, context):
        if not re.search(r"^\d+$", context["other_person_id"]):
            message = "Malformed person ID '{0}'"
            raise InvalidMergeError(message.format(context["other_person_id"]))
        if context["person"].pk == int(context["other_person_id"]):
            message = "You can't merge a person ({0}) with themself ({1})"
            raise InvalidMergeError(
                message.format(context["person"].pk, context["other_person_id"])
            )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["person"] = get_object_or_404(
            Person, id=self.kwargs["person_id"]
        )
        context["other_person_id"] = self.request.POST.get("other_person", "")
        return context

    def post(self, request, *args, **kwargs):
        context = self.get_context_data()

        # Check that the person IDs are well-formed:
        try:
            self.validate(context)
        except InvalidMergeError as e:
            context["error_message"] = e
            return self.render_to_response(context)

        with transaction.atomic():
            secondary_person = get_object_or_404(
                Person, id=context["other_person_id"]
            )

            try:
                merged_person = self.do_merge(
                    context["person"], secondary_person
                )
            except NotStandingValidationError:
                return HttpResponseRedirect(
                    reverse(
                        "person-merge-correct-not-standing",
                        kwargs={
                            "person_id": context["person"].pk,
                            "other_person_id": context["other_person_id"],
                        },
                    )
                )

        # And redirect to the primary person with the merged data:
        return HttpResponseRedirect(merged_person.get_absolute_url())


class CorrectNotStandingMergeView(
    GroupRequiredMixin, TemplateView, MergePeopleMixin
):
    template_name = "people/correct_not_standing_in_merge.html"
    required_group_name = TRUSTED_TO_MERGE_GROUP_NAME

    def extract_not_standing_edit(self, election, versions):
        versions_json = versions
        for version in versions_json:
            try:
                membership = version["data"]["standing_in"][election.slug]
                if membership is None:
                    return version
            except KeyError:
                continue
        return None

    def populate_not_standing_list(self, person, person_not_standing):
        for membership in person.memberships.all():
            if (
                membership.ballot.election
                in person_not_standing.not_standing.all()
            ):
                self.not_standing_elections.append(
                    {
                        "election": membership.ballot.election,
                        "person_standing": person,
                        "person_standing_ballot": membership.ballot,
                        "person_not_standing": person_not_standing,
                        "version": self.extract_not_standing_edit(
                            membership.ballot.election,
                            person_not_standing.versions,
                        ),
                    }
                )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["person_a"] = get_object_or_404(
            Person, id=self.kwargs["person_id"]
        )
        context["person_b"] = get_object_or_404(
            Person, id=self.kwargs["other_person_id"]
        )

        self.not_standing_elections = []
        self.populate_not_standing_list(
            context["person_a"], context["person_b"]
        )
        self.populate_not_standing_list(
            context["person_b"], context["person_a"]
        )
        context["not_standing_elections"] = self.not_standing_elections
        return context

    def post(self, request, *args, **kwargs):
        context = self.get_context_data()

        with transaction.atomic():
            for pair in context["not_standing_elections"]:
                pair["person_not_standing"].not_standing.remove(
                    pair["election"]
                )
        merged_person = self.do_merge(context["person_a"], context["person_b"])

        # And redirect to the primary person with the merged data:
        return HttpResponseRedirect(merged_person.get_absolute_url())


class UpdatePersonView(LoginRequiredMixin, ProcessInlineFormsMixin, UpdateView):
    template_name = "candidates/person-edit.html"
    queryset = Person.objects.all()
    pk_url_kwarg = "person_id"
    form_class = UpdatePersonForm
    inline_formset_classes = {
        "identifiers_formset": PersonIdentifierFormsetFactory,
        "memberships_formset": PersonMembershipFormsetFactory,
    }

    def get_inline_formset_kwargs(self, formset_name):
        kwargs = {}

        if formset_name == "memberships_formset":
            kwargs.update({"form_kwargs": {"user": self.request.user}})

        if formset_name == "identifiers_formset":
            model = self.inline_formset_classes["identifiers_formset"].model
            kwargs.update({"queryset": model.objects.editable_value_types()})

        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        person = self.object
        context["person"] = person

        context["person_edits_allowed"] = person.user_can_edit(
            self.request.user
        )
        context["current_locked_ballots"] = person.memberships.filter(
            ballot__election__current=True, ballot__candidates_locked=True
        )
        context["versions"] = get_version_diffs(person.versions)

        return context

    def form_valid(self, all_forms):
        form = all_forms["form"]

        if not (settings.EDITS_ALLOWED or self.request.user.is_staff):
            return HttpResponseRedirect(reverse("all-edits-disallowed"))

        context = self.get_context_data()
        if not context["person_edits_allowed"]:
            raise PermissionDenied

        identifiers_formset = all_forms["identifiers_formset"]
        membership_formset = all_forms["memberships_formset"]

        with transaction.atomic():
            person = context["person"]
            identifiers_formset.instance = person
            identifiers_formset.save()

            membership_formset.save()
            person = form.save(user=self.request.user)
            change_metadata = get_change_metadata(
                self.request, form.cleaned_data.pop("source")
            )
            person.record_version(change_metadata)
            person.save()
            LoggedAction.objects.create(
                user=self.request.user,
                person=person,
                action_type=ActionType.PERSON_UPDATE,
                ip_address=get_client_ip(self.request),
                popit_person_new_version=change_metadata["version_id"],
                source=change_metadata["information_source"],
            )

            # Add a message to be displayed after redirect:
            messages.add_message(
                self.request,
                messages.SUCCESS,
                get_call_to_action_flash_message(person, new_person=False),
                extra_tags="safe do-something-else",
            )

        return HttpResponseRedirect(
            reverse("person-view", kwargs={"person_id": person.id})
        )


class PersonSplitView(FormView):
    template_name = "people/split_person.html"
    form_class = PersonSplitForm

    def get_review_url(self):
        person_id = self.kwargs.get("person_id")
        return reverse_lazy(
            "review_split_person", kwargs={"person_id": person_id}
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["person"] = self.get_person()
        context["person_id"] = self.kwargs["person_id"]
        context["formset"] = self.get_form()
        return context

    def get_initial_data(self, form_class=None):
        person = self.get_person()
        #: TO DO: Figure out how to return attribute names and values only for those that are not empty
        return [
            {"attribute_name": "name", "attribute_value": person.name},
            # {"attribute_name": "image", "attribute_value": person.image.image if person.image else None},
            {"attribute_name": "gender", "attribute_value": person.gender},
            # {
            # "attribute_name": "birth_date",
            # "attribute_value": person.birth_date if person.birth_date else None,
            # },
            # {
            #     "attribute_name": "death_date",
            #     "attribute_value": person.death_date if person.death_date else None,
            # },
            # {"attribute_name": "summary", "attribute_value": person.summary if person.summary else None },
            # {
            # "attribute_name": "biography",
            # "attribute_value": person.biography if person.biography else None,
            # },
            # {
            # "attribute_name": "other_names",
            # "attribute_value": person.other_names.all if person.other_names.all else None,
            # },
            # {
            #     "attribute_name": "memberships",
            #     "attribute_value": person.memberships.all if person.memberships.all else None,
            # },
        ]

    def get_form(self, form_class=None):
        return PersonSplitFormSet(
            initial=self.get_initial_data(),
        )

    def get_person(self):
        person_id = self.kwargs.get("person_id")
        return get_object_or_404(Person, pk=person_id)

    def form_valid(self, formset):
        choices = {
            "keep": [],
            "move": [],
            "both": [],
        }
        for form in formset:
            attribute_name = form.cleaned_data["attribute_name"]
            attribute_value = form.cleaned_data["attribute_value"]
            choice = form.cleaned_data["choice"]
            person_id = self.kwargs.get("person_id")
            if choice == "keep":
                choices["keep"].append({attribute_name: attribute_value})
            elif choice == "move":
                choices["move"].append({attribute_name: attribute_value})
            elif choice == "both":
                choices["both"].append({attribute_name: attribute_value})
        if choices:
            self.request.session["choices"] = choices
            self.request.session["person_id"] = person_id
            return redirect(self.get_review_url())
        return self.form_invalid(formset)

    def post(self, request, *args, **kwargs):
        formset = PersonSplitFormSet(request.POST)
        if formset.is_valid():
            return self.form_valid(formset)
        return self.form_invalid(formset)


class ReviewPersonSplitView(TemplateView):
    template_name = "people/review_split_person.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["choices"] = self.request.session.get("choices", {})
        context["person"] = get_object_or_404(
            Person, pk=self.request.session.get("person_id")
        )
        return context


class NewPersonSelectElectionView(LoginRequiredMixin, FormView):
    """
    For when we know new person's name, but not the election they are standing
    in.  This is normally because we've not come via a post page to add a new
    person (e.g., we've come from the search results page).
    """

    template_name = "candidates/person-create-select-election.html"
    form_class = SelectBallotForm

    def get_context_data(self, **kwargs):
        context = super(NewPersonSelectElectionView, self).get_context_data(
            **kwargs
        )
        context["name"] = self.request.GET.get("name")[:150]
        return context

    def form_valid(self, form):
        context = self.get_context_data()
        name = context["name"]
        ballot_paper_id = form.cleaned_data["ballot"].ballot_paper_id
        return HttpResponseRedirect(
            reverse(
                "person-create", kwargs={"ballot_paper_id": ballot_paper_id}
            )
            + f"?name={name}"
        )


class NewPersonView(
    ProcessInlineFormsMixin, ElectionMixin, LoginRequiredMixin, FormView
):
    template_name = "candidates/person-create.html"
    form_class = NewPersonForm
    inline_formset_classes = {
        "identifiers_formset": PersonIdentifierFormsetFactory
    }

    def get_initial(self):
        result = super().get_initial()
        result["ballot_paper_id"] = self.get_ballot()
        result["name"] = self.request.GET.get("name")
        return result

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        context["add_candidate_form"] = context["form"]

        return context

    def form_valid(self, all_forms):
        form = all_forms["form"]
        identifiers_formset = all_forms["identifiers_formset"]
        with transaction.atomic():
            person = form.save()

            identifiers_formset.instance = person
            identifiers_formset.save()

            change_metadata = get_change_metadata(
                self.request, form.cleaned_data["source"]
            )
            person.record_version(change_metadata)
            person.save()
            LoggedAction.objects.create(
                user=self.request.user,
                person=person,
                action_type=ActionType.PERSON_CREATE,
                ip_address=get_client_ip(self.request),
                popit_person_new_version=change_metadata["version_id"],
                source=change_metadata["information_source"],
            )

            # Add a message to be displayed after redirect:
            messages.add_message(
                self.request,
                messages.SUCCESS,
                get_call_to_action_flash_message(person, new_person=True),
                extra_tags="safe do-something-else",
            )

        return HttpResponseRedirect(
            reverse("person-view", kwargs={"person_id": person.id})
        )
