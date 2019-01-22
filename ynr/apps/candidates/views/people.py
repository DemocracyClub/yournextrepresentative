import json
import re

from slugify import slugify

from django.conf import settings
from django.contrib import messages
from django.core.urlresolvers import reverse
from django.db import transaction
from django.http import (
    HttpResponseRedirect,
    HttpResponsePermanentRedirect,
    Http404,
)
from django.shortcuts import get_object_or_404
from django.template.loader import render_to_string
from django.utils.decorators import method_decorator
from django.utils.http import urlquote
from django.utils.translation import ugettext as _
from django.views.decorators.cache import cache_control
from django.views.generic import FormView, TemplateView, View

from braces.views import LoginRequiredMixin

from auth_helpers.views import GroupRequiredMixin, user_in_group
from elections.models import Election
from elections.mixins import ElectionMixin

from ..diffs import get_version_diffs
from ..election_specific import additional_merge_actions
from .version_data import get_client_ip, get_change_metadata
from people.forms import (
    NewPersonForm,
    UpdatePersonForm,
    PersonIdentifierFormsetFactory,
)
from candidates.forms import SingleElectionForm
from ..models import LoggedAction, PersonRedirect, TRUSTED_TO_MERGE_GROUP_NAME
from ..models.auth import check_creation_allowed, check_update_allowed
from ..models.versions import (
    revert_person_from_version_data,
    get_person_as_version_data,
)
from ..models import merge_popit_people
from .helpers import (
    get_field_groupings,
    get_person_form_fields,
    ProcessInlineFormsMixin,
)
from people.models import Person


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
                        "person-create", kwargs={"election": election_data.slug}
                    ),
                    election_data.name,
                )
                for election_data in Election.objects.filter(
                    postextraelection__membership__person=person, current=True
                ).distinct()
            ],
        },
    )


class PersonView(TemplateView):
    template_name = "candidates/person-view.html"

    @method_decorator(cache_control(max_age=(60 * 20)))
    def dispatch(self, *args, **kwargs):
        return super().dispatch(*args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        path = self.person.get_absolute_url()
        context["redirect_after_login"] = urlquote(path)
        context["canonical_url"] = self.request.build_absolute_uri(path)
        context["person"] = self.person

        context["elections_to_list"] = Election.objects.filter(
            postextraelection__membership__person=self.person
        ).order_by("-election_date")

        context["last_candidacy"] = self.person.last_candidacy
        context["election_to_show"] = None
        context["has_current_elections"] = (
            context["elections_to_list"].filter(current=True).exists()
        )
        context["simple_fields"] = [
            field.name for field in settings.SIMPLE_POPOLO_FIELDS
        ]
        personal_fields, demographic_fields = get_field_groupings()
        context["has_demographics"] = any(
            demographic in context["simple_fields"]
            for demographic in demographic_fields
        )

        return context

    def get(self, request, *args, **kwargs):
        person_id = self.kwargs["person_id"]
        try:
            self.person = Person.objects.prefetch_related(
                "links", "tmp_person_identifiers"
            ).get(pk=person_id)
        except Person.DoesNotExist:
            try:
                return self.get_person_redirect(person_id)
            except PersonRedirect.DoesNotExist:
                raise Http404(
                    _("No person found with ID {person_id}").format(
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

            versions = json.loads(person.versions)

            data_to_revert_to = None
            for version in versions:
                if version["version_id"] == version_id:
                    data_to_revert_to = version["data"]
                    break

            if not data_to_revert_to:
                message = _("Couldn't find the version {0} of person {1}")
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
                action_type="person-revert",
                ip_address=get_client_ip(self.request),
                popit_person_new_version=change_metadata["version_id"],
                source=change_metadata["information_source"],
            )

        return HttpResponseRedirect(
            reverse("person-view", kwargs={"person_id": person_id})
        )


class MergePeopleView(GroupRequiredMixin, View):

    http_method_names = ["post"]
    required_group_name = TRUSTED_TO_MERGE_GROUP_NAME

    def merge(self, primary_person, secondary_person, change_metadata):

        with additional_merge_actions(primary_person, secondary_person):
            # Merge the reduced JSON representations:
            merged_person_version_data = merge_popit_people(
                get_person_as_version_data(primary_person),
                get_person_as_version_data(secondary_person),
            )
            revert_person_from_version_data(
                primary_person, merged_person_version_data, part_of_merge=True
            )
        # Make sure the secondary person's version history is appended, so it
        # isn't lost.
        primary_person_versions = json.loads(primary_person.versions)
        primary_person_versions += json.loads(secondary_person.versions)
        primary_person.versions = json.dumps(primary_person_versions)
        primary_person.record_version(change_metadata)
        primary_person.save()
        # Change the secondary person's images to point at the primary
        # person instead:
        existing_primary_image = primary_person.images.filter(
            is_primary=True
        ).exists()
        for image in secondary_person.images.all():
            image.person = primary_person
            if existing_primary_image:
                image.is_primary = False
            image.save()

    def post(self, request, *args, **kwargs):
        # Check that the person IDs are well-formed:
        primary_person_id = self.kwargs["person_id"]
        secondary_person_id = self.request.POST["other"]
        if not re.search("^\d+$", secondary_person_id):
            message = _("Malformed person ID '{0}'")
            raise ValueError(message.format(secondary_person_id))
        if primary_person_id == secondary_person_id:
            message = _("You can't merge a person ({0}) with themself ({1})")
            raise ValueError(
                message.format(primary_person_id, secondary_person_id)
            )
        with transaction.atomic():
            primary_person, secondary_person = [
                get_object_or_404(Person, id=person_id)
                for person_id in (primary_person_id, secondary_person_id)
            ]
            primary_person = primary_person
            secondary_person = secondary_person
            change_metadata = get_change_metadata(
                self.request,
                _("After merging person {0}").format(secondary_person.id),
            )
            self.merge(primary_person, secondary_person, change_metadata)
            # Now we delete the old person:
            secondary_person.delete()
            # Create a redirect from the old person to the new person:
            PersonRedirect.objects.create(
                old_person_id=secondary_person_id,
                new_person_id=primary_person_id,
            )
            # Log that that action has taken place, and will be shown in
            # the recent changes, leaderboards, etc.
            LoggedAction.objects.create(
                user=self.request.user,
                action_type="person-merge",
                ip_address=get_client_ip(self.request),
                popit_person_new_version=change_metadata["version_id"],
                person=primary_person,
                source=change_metadata["information_source"],
            )
        # And redirect to the primary person with the merged data:
        return HttpResponseRedirect(
            reverse(
                "person-view",
                kwargs={
                    "person_id": primary_person_id,
                    "ignored_slug": slugify(primary_person.name),
                },
            )
        )


class UpdatePersonView(ProcessInlineFormsMixin, LoginRequiredMixin, FormView):
    template_name = "candidates/person-edit.html"
    form_class = UpdatePersonForm
    inline_formset_classes = {
        "identifiers_formset": PersonIdentifierFormsetFactory
    }

    def get_inline_formset_kwargs(self, formset_name):
        if formset_name == "identifiers_formset":
            return {"instance": Person.objects.get(pk=self.kwargs["person_id"])}

    def get_initial(self):
        initial_data = super().get_initial()
        person = get_object_or_404(Person, pk=self.kwargs["person_id"])
        initial_data.update(person.get_initial_form_data())
        initial_data["person"] = person
        return initial_data

    def get_context_data(self, **kwargs):

        context = super().get_context_data(**kwargs)

        person = get_object_or_404(Person, pk=self.kwargs["person_id"])
        context["person"] = person

        context["user_can_merge"] = user_in_group(
            self.request.user, TRUSTED_TO_MERGE_GROUP_NAME
        )

        context["versions"] = get_version_diffs(json.loads(person.versions))

        context = get_person_form_fields(context, context["form"])

        return context

    def form_valid(self, all_forms):
        form = all_forms["form"]

        if not (settings.EDITS_ALLOWED or self.request.user.is_staff):
            return HttpResponseRedirect(reverse("all-edits-disallowed"))

        context = self.get_context_data()
        identifiers_formset = all_forms["identifiers_formset"]

        with transaction.atomic():

            person = context["person"]
            identifiers_formset.instance = person
            identifiers_formset.save()

            old_name = person.name
            old_candidacies = person.current_candidacies
            person.update_from_form(form)
            new_name = person.name
            new_candidacies = person.current_candidacies
            check_update_allowed(
                self.request.user,
                old_name,
                old_candidacies,
                new_name,
                new_candidacies,
            )
            change_metadata = get_change_metadata(
                self.request, form.cleaned_data.pop("source")
            )
            person.record_version(change_metadata)
            person.save()
            LoggedAction.objects.create(
                user=self.request.user,
                person=person,
                action_type="person-update",
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


class NewPersonSelectElectionView(LoginRequiredMixin, TemplateView):
    """
    For when we know new person's name, but not the election they are standing
    in.  This is normally because we've not come via a post page to add a new
    person (e.g., we've come from the search results page).
    """

    template_name = "candidates/person-create-select-election.html"

    def get_context_data(self, **kwargs):
        context = super(NewPersonSelectElectionView, self).get_context_data(
            **kwargs
        )
        context["name"] = self.request.GET.get("name")
        elections = []
        local_elections = []
        for election in Election.objects.filter(current=True).order_by("slug"):
            election_type = election.slug.split(".")[0]
            if election_type == "local":
                election.type_name = "Local Elections"
                local_elections.append(election)
            else:
                election.type_name = election.name
                elections.append(election)
        elections += local_elections
        context["elections"] = elections

        return context


class NewPersonView(
    ProcessInlineFormsMixin, ElectionMixin, LoginRequiredMixin, FormView
):
    template_name = "candidates/person-create.html"
    form_class = NewPersonForm
    inline_formset_classes = {
        "identifiers_formset": PersonIdentifierFormsetFactory
    }

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["election"] = self.election
        return kwargs

    def get_initial(self):
        result = super().get_initial()
        result["standing_" + self.election] = "standing"
        result["name"] = self.request.GET.get("name")
        return result

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        context["add_candidate_form"] = context["form"]

        context = get_person_form_fields(context, context["add_candidate_form"])
        return context

    def form_valid(self, all_forms):
        form = all_forms["form"]
        identifiers_formset = all_forms["identifiers_formset"]
        context = self.get_context_data()
        with transaction.atomic():

            person = Person.create_from_form(form)

            identifiers_formset.instance = person
            identifiers_formset.save()

            check_creation_allowed(
                self.request.user, person.current_candidacies
            )
            change_metadata = get_change_metadata(
                self.request, form.cleaned_data["source"]
            )
            person.record_version(change_metadata)
            person.save()
            LoggedAction.objects.create(
                user=self.request.user,
                person=person,
                action_type="person-create",
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


class SingleElectionFormView(LoginRequiredMixin, FormView):
    template_name = "candidates/person-edit-add-single-election.html"
    form_class = SingleElectionForm

    def get_initial(self):
        initial_data = super().get_initial()
        election = get_object_or_404(
            Election.objects.all(), slug=self.kwargs["election"]
        )
        initial_data["election"] = election
        return initial_data
