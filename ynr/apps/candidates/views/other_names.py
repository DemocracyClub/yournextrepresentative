from candidates.models import LoggedAction
from candidates.models.db import ActionType
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.contenttypes.models import ContentType
from django.db import transaction
from django.http import Http404, JsonResponse
from django.urls import reverse
from django.utils.functional import cached_property
from django.views.generic import CreateView, DeleteView, ListView, UpdateView
from people.forms.forms import OtherNameForm, SopnNameForm
from people.models import Person
from people.notifications import send_sopn_name_change_notification
from popolo.models import Membership, OtherName

from .version_data import get_change_metadata, get_client_ip


class PersonMixin(object):
    @cached_property
    def person(self):
        return Person.objects.get(pk=self.kwargs["person_id"])

    def get_success_url(self):
        return reverse(
            "person-other-names", kwargs={"person_id": self.person.id}
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["person"] = self.person
        return context


class PersonOtherNamesView(PersonMixin, ListView):
    model = OtherName
    template_name = "candidates/othername_list.html"

    def get_queryset(self):
        qs = super().get_queryset()
        ct = ContentType.objects.get_for_model(Person)
        return qs.filter(
            content_type=ct, object_id=self.kwargs["person_id"]
        ).order_by("name", "start_date", "end_date")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        context["memberships"] = (
            Person.objects.get(pk=self.kwargs["person_id"])
            .memberships.select_related("ballot__sopn")
            .select_related("ballot__election")
            .select_related("ballot__post")
            .order_by("-ballot__election__election_date")
        )

        return context


class PersonSopnNamesEditView(LoginRequiredMixin, PersonMixin, UpdateView):
    model = Membership
    form_class = SopnNameForm
    template_name = "candidates/sopnnames_edit.html"
    raise_exception = True

    def get_object(self, queryset=None):
        membership = Membership.objects.select_related(
            "ballot__sopn",
            "ballot__election",
            "ballot__post",
        ).get(
            pk=self.kwargs["membership_id"],
            person=self.person,
        )

        # only allow editing the SOPN names if the ballot has a SOPN
        if not hasattr(membership.ballot, "sopn"):
            raise Http404("No SOPN exists for this ballot")

        return membership

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["user"] = self.request.user
        return kwargs

    def form_valid(self, form):
        initial_first = self.get_object().sopn_first_names or ""
        initial_last = self.get_object().sopn_last_name or ""
        initial_name = (f"{initial_first} {initial_last}").strip()

        new_first = form.cleaned_data.get("sopn_first_names") or ""
        new_last = form.cleaned_data.get("sopn_last_name") or ""
        new_name = (f"{new_first} {new_last}").strip()

        name_changed = initial_name != new_name

        with transaction.atomic():
            result = super().form_valid(form)
            LoggedAction.objects.create(
                user=self.request.user,
                person=self.person,
                action_type=ActionType.CANDIDACY_SOPN_NAMES_UPDATE,
                ip_address=get_client_ip(self.request),
                ballot=self.object.ballot,
                source="SOPN",
            )

        if self.object.ballot.candidates_locked and name_changed:
            send_sopn_name_change_notification(
                self.person,
                initial_name,
                new_name,
                self.object.ballot,
                self.request.user.username,
            )

        return result


class PersonOtherNameCreateView(LoginRequiredMixin, PersonMixin, CreateView):
    model = OtherName
    form_class = OtherNameForm
    template_name = "candidates/othername_new.html"
    raise_exception = True

    def post(self, request, *args, **kwargs):
        form = self.get_form()
        self.object = None
        form.instance.content_object = self.person
        if form.is_valid():
            return self.form_valid(form)
        return self.form_invalid(form)

    def form_valid(self, form):
        with transaction.atomic():
            # This is similar to the example here:
            #   https://docs.djangoproject.com/en/1.8/topics/class-based-views/generic-editing/#models-and-request-user

            result = super(PersonOtherNameCreateView, self).form_valid(form)
            change_metadata = get_change_metadata(
                self.request, form.cleaned_data["source"]
            )
            self.person.record_version(change_metadata)
            self.person.save()
            LoggedAction.objects.create(
                user=self.request.user,
                person=self.person,
                action_type=ActionType.PERSON_OTHER_NAME_CREATE,
                ip_address=get_client_ip(self.request),
                popit_person_new_version=change_metadata["version_id"],
                source=change_metadata["information_source"],
            )
            """
            On the bulk edit page this view is inlined and the data
            sent over ajax so we have to return an ajax response, and
            also the new list of names so we can show the new list of
            alternative names as a confirmation it's all worked
            """
            if self.request.headers.get("x-requested-with") == "XMLHttpRequest":
                qs = super().get_queryset()
                ct = ContentType.objects.get_for_model(Person)
                qs = qs.filter(
                    content_type=ct, object_id=self.person.id
                ).order_by("name", "start_date", "end_date")
                data = {
                    "success": True,
                    "names": list(qs.values_list("name", flat=True)),
                }
                return JsonResponse(data)
            return result

    def form_invalid(self, form):
        result = super(PersonOtherNameCreateView, self).form_invalid(form)
        if self.request.headers.get("x-requested-with") == "XMLHttpRequest":
            data = {"success": False, "errors": form.errors}
            return JsonResponse(data)

        return result


class PersonOtherNameDeleteView(LoginRequiredMixin, PersonMixin, DeleteView):
    model = OtherName
    raise_exception = True

    def form_valid(self, request, *args, **kwargs):
        with transaction.atomic():
            result_redirect = super().delete(request, *args, **kwargs)
            change_metadata = get_change_metadata(
                self.request, self.request.POST["source"]
            )
            self.person.record_version(change_metadata)
            self.person.save()
            LoggedAction.objects.create(
                user=self.request.user,
                person=self.person,
                action_type=ActionType.PERSON_OTHER_NAME_DELETE,
                ip_address=get_client_ip(self.request),
                popit_person_new_version=change_metadata["version_id"],
                source=change_metadata["information_source"],
            )
            return result_redirect


class PersonOtherNameUpdateView(LoginRequiredMixin, PersonMixin, UpdateView):
    model = OtherName
    form_class = OtherNameForm
    template_name = "candidates/othername_edit.html"
    raise_exception = True

    def form_valid(self, form):
        with transaction.atomic():
            result = super(PersonOtherNameUpdateView, self).form_valid(form)
            change_metadata = get_change_metadata(
                self.request, form.cleaned_data["source"]
            )
            self.person.record_version(change_metadata)
            self.person.save()
            LoggedAction.objects.create(
                user=self.request.user,
                person=self.person,
                action_type=ActionType.PERSON_OTHER_NAME_UPDATE,
                ip_address=get_client_ip(self.request),
                popit_person_new_version=change_metadata["version_id"],
                source=change_metadata["information_source"],
            )
            return result
