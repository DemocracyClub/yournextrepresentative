from braces.views import LoginRequiredMixin
from django.contrib import messages
from django.db import transaction
from django.db.models import F
from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404
from django.urls import reverse
from django.views.generic import RedirectView, TemplateView

from bulk_adding import forms, helpers
from bulk_adding.models import RawPeople
from candidates.models import Ballot, LoggedAction
from candidates.models.db import EditType
from candidates.views.version_data import get_client_ip
from moderation_queue.models import SuggestedPostLock
from official_documents.models import OfficialDocument
from official_documents.views import get_add_from_document_cta_flash_message
from parties.models import Party
from people.models import Person


class BulkAddSOPNRedirectView(RedirectView):
    def get_redirect_url(self, *args, **kwargs):
        ballot = Ballot.objects.get(ballot_paper_id=kwargs["ballot_paper_id"])
        return ballot.get_bulk_add_url()


class BaseSOPNBulkAddView(LoginRequiredMixin, TemplateView):
    # required_group_name = models.TRUSTED_TO_BULK_ADD_GROUP_NAME

    def add_election_and_post_to_context(self, context):
        if not hasattr(self, "ballot"):
            self.ballot = get_object_or_404(
                Ballot, ballot_paper_id=context["ballot_paper_id"]
            )
        context["ballot"] = self.ballot
        context["post"] = self.ballot.post
        context["election_obj"] = self.ballot.election
        kwargs = {"exclude_deregistered": True, "include_description_ids": True}
        if not self.request.POST:
            kwargs["include_non_current"] = False
        register = context["post"].party_set.slug.upper()
        context["parties"] = Party.objects.register(register).party_choices(
            **kwargs
        )
        try:
            context["official_document"] = self.ballot.sopn
        except OfficialDocument.DoesNotExist:
            context["official_document"] = None
        self.official_document = context["official_document"]
        return context

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(self.add_election_and_post_to_context(context))

        people_set = set()
        for membership in context["ballot"].membership_set.all():
            person = membership.person
            person.party = membership.party

            people_set.add(person)

        known_people = list(people_set)
        known_people.sort(key=lambda i: i.last_name_guess)
        context["known_people"] = known_people
        return context

    def remaining_posts_for_sopn(self):
        return OfficialDocument.objects.filter(
            source_url=self.official_document.source_url,
            ballot__election=F("ballot__election"),
            ballot__suggestedpostlock=None,
        )

    def post(self, request, *args, **kwargs):
        context = self.get_context_data(**kwargs)
        if context["formset"].is_valid():
            return self.form_valid(context)
        else:
            return self.form_invalid(context)


class BulkAddSOPNView(BaseSOPNBulkAddView):
    template_name = "bulk_add/sopns/add_form.html"

    def get(self, request, *args, **kwargs):
        if not request.GET.get("edit"):
            ballot_qs = Ballot.objects.filter(
                ballot_paper_id=kwargs["ballot_paper_id"]
            ).select_related("post", "election")
            if ballot_qs.exists():
                self.ballot = ballot_qs.get()
                if hasattr(ballot_qs.get(), "rawpeople"):
                    if self.ballot.rawpeople.is_trusted:
                        return HttpResponseRedirect(
                            self.ballot.get_bulk_add_review_url()
                        )
        return super().get(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        form_kwargs = {
            "parties": context["parties"],
            "party_set": context["post"].party_set,
            "ballot": context["ballot"],
        }

        if hasattr(context["ballot"], "rawpeople"):
            form_kwargs.update(context["ballot"].rawpeople.as_form_kwargs())

        if (
            "official_document" in context
            and context["official_document"] is not None
        ):
            form_kwargs["source"] = context["official_document"].source_url

        if self.request.POST:
            context["formset"] = forms.BulkAddFormSet(
                self.request.POST, **form_kwargs
            )
        else:
            context["formset"] = forms.BulkAddFormSet(**form_kwargs)

        return context

    def form_valid(self, context):
        raw_ballot_data = []
        for form_data in context["formset"].cleaned_data:
            if not form_data or form_data.get("DELETE"):
                continue
            if "__" in form_data["party"]:
                party_id, description_id = form_data["party"].split("__")
            else:
                party_id = form_data["party"]
                description_id = None

            raw_ballot_data.append(
                {
                    "name": form_data["name"],
                    "party_id": party_id,
                    "description_id": description_id,
                }
            )

        RawPeople.objects.update_or_create(
            ballot=context["ballot"],
            defaults={
                "data": raw_ballot_data,
                "source": context["official_document"].source_url[:512],
                "source_type": RawPeople.SOURCE_BULK_ADD_FORM,
            },
        )

        return HttpResponseRedirect(context["ballot"].get_bulk_add_review_url())

    def form_invalid(self, context):
        return self.render_to_response(context)


class BulkAddSOPNReviewView(BaseSOPNBulkAddView):
    template_name = "bulk_add/sopns/add_review_form.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        initial = []
        if hasattr(context["ballot"], "rawpeople"):
            raw_ballot_data = context["ballot"].rawpeople.data
        else:
            # Race condition! Someone else has processes this area
            # between page views. Best just show the data we have.
            raw_ballot_data = []

        for candidacy in raw_ballot_data:
            form = {}
            party = Party.objects.get(ec_id=candidacy["party_id"])

            form["party_description_text"] = party.name
            if candidacy.get("description_id"):
                party_description = party.descriptions.get(
                    pk=candidacy["description_id"]
                )
                form["party_description"] = party_description
                form["party_description_text"] = party_description.description

            form["name"] = candidacy["name"]
            form["party"] = party.ec_id
            form["source"] = context["official_document"].source_url
            initial.append(form)

        if self.request.POST:
            context["formset"] = forms.BulkAddReviewFormSet(
                self.request.POST,
                parties=context["parties"],
                ballot=context["ballot"],
            )
        else:
            context["formset"] = forms.BulkAddReviewFormSet(
                initial=initial,
                parties=context["parties"],
                ballot=context["ballot"],
            )
        return context

    def form_valid(self, context):

        with transaction.atomic():
            for person_form in context["formset"]:
                data = person_form.cleaned_data

                if data.get("select_person") == "_new":
                    # Add a new person
                    person = helpers.add_person(self.request, data)
                else:
                    person = Person.objects.get(pk=int(data["select_person"]))

                party = Party.objects.get(ec_id=data["party"])
                helpers.update_person(
                    request=self.request,
                    person=person,
                    party=party,
                    ballot=context["ballot"],
                    source=data["source"],
                    party_description=data["party_description"],
                )

            # ballot has changed so we should remove any out of date suggestions
            ballot = Ballot.objects.get(
                ballot_paper_id=context["ballot"].ballot_paper_id
            )
            ballot.delete_outdated_suggested_locks()

            if self.request.POST.get("suggest_locking") == "on":
                SuggestedPostLock.objects.create(
                    user=self.request.user, ballot=ballot
                )

                LoggedAction.objects.create(
                    user=self.request.user,
                    action_type="suggest-ballot-lock",
                    ip_address=get_client_ip(self.request),
                    ballot=ballot,
                    source="Suggested after bulk adding",
                    edit_type=EditType.BULK_ADD.name,
                )

                if hasattr(ballot, "rawpeople"):
                    # Delete the raw import, as it's no longer useful
                    ballot.rawpeople.delete()

        messages.add_message(
            self.request,
            messages.SUCCESS,
            get_add_from_document_cta_flash_message(
                self.official_document, self.remaining_posts_for_sopn()
            ),
            extra_tags="safe do-something-else",
        )

        remaining_qs = self.remaining_posts_for_sopn().exclude(
            pk=self.official_document.pk
        )
        if remaining_qs.exists():
            url = reverse(
                "posts_for_document", kwargs={"pk": self.official_document.pk}
            )
        else:
            url = context["ballot"].get_absolute_url()
        return HttpResponseRedirect(url)

    def form_invalid(self, context):
        return self.render_to_response(context)
