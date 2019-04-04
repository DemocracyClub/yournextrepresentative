from braces.views import LoginRequiredMixin
from django.contrib import messages
from django.core.urlresolvers import reverse
from django.db import transaction
from django.db.models import F
from django.http import HttpResponseRedirect
from django.views.generic import RedirectView, TemplateView

from bulk_adding import forms, helpers
from bulk_adding.models import RawPeople
from candidates.models import PostExtraElection, LoggedAction
from candidates.views import get_client_ip
from elections.models import Election
from moderation_queue.models import SuggestedPostLock
from official_documents.models import OfficialDocument
from official_documents.views import get_add_from_document_cta_flash_message
from parties.models import Party
from people.models import Person
from popolo.models import Post


class BulkAddSOPNRedirectView(RedirectView):
    def get_redirect_url(self, *args, **kwargs):
        return reverse(
            "bulk_add_from_sopn",
            kwargs={
                "election": kwargs["election"],
                "post_id": kwargs["post_id"],
            },
        )


class BaseSOPNBulkAddView(LoginRequiredMixin, TemplateView):
    # required_group_name = models.TRUSTED_TO_BULK_ADD_GROUP_NAME

    def add_election_and_post_to_context(self, context):
        context["post"] = Post.objects.get(slug=context["post_id"])
        context["election_obj"] = Election.objects.get(slug=context["election"])
        context["post_election"] = context[
            "election_obj"
        ].postextraelection_set.get(post=context["post"])
        kwargs = {"exclude_deregistered": True, "include_description_ids": True}
        if not self.request.POST:
            kwargs["include_non_current"] = False
        register = context["post"].party_set.slug.upper()
        context["parties"] = Party.objects.register(register).party_choices(
            **kwargs
        )
        context["official_document"] = OfficialDocument.objects.filter(
            post_election=context["post_election"]
        ).first()
        self.official_document = context["official_document"]
        return context

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(self.add_election_and_post_to_context(context))

        people_set = set()
        for membership in context["post_election"].membership_set.all():
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
            post_election__election=F("post_election__election"),
            post_election__suggestedpostlock=None,
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
            pee_qs = PostExtraElection.objects.filter(
                election__slug=kwargs["election"], post__slug=kwargs["post_id"]
            )
            if pee_qs.exists():
                pee = pee_qs.get()
                if hasattr(pee_qs.get(), "rawpeople"):
                    if pee.rawpeople.is_trusted:
                        return HttpResponseRedirect(
                            reverse("bulk_add_sopn_review", kwargs=kwargs)
                        )
        return super().get(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        form_kwargs = {
            "parties": context["parties"],
            "party_set": context["post"].party_set,
            "ballot": context["post_election"],
        }

        if hasattr(context["post_election"], "rawpeople"):
            form_kwargs.update(
                context["post_election"].rawpeople.as_form_kwargs()
            )

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
            ballot=context["post_election"],
            defaults={
                "data": raw_ballot_data,
                "source": context["official_document"].source_url,
                "source_type": RawPeople.SOURCE_BULK_ADD_FORM,
            },
        )

        return HttpResponseRedirect(
            reverse(
                "bulk_add_sopn_review",
                kwargs={
                    "election": context["election"],
                    "post_id": context["post_id"],
                },
            )
        )

    def form_invalid(self, context):
        return self.render_to_response(context)


class BulkAddSOPNReviewView(BaseSOPNBulkAddView):
    template_name = "bulk_add/sopns/add_review_form.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        initial = []
        if hasattr(context["post_election"], "rawpeople"):
            raw_ballot_data = context["post_election"].rawpeople.data
        else:
            # Race condition! Someone else has processes this area
            # between page views. Best just show the data we have.
            raw_ballot_data = []

        for candidacy in raw_ballot_data:
            form = {}
            party = Party.objects.get(ec_id=candidacy["party_id"])
            if candidacy.get("description_id"):
                form["party_description"] = party.descriptions.get(
                    pk=candidacy["description_id"]
                ).description
            else:
                form["party_description"] = party.name
            form["name"] = candidacy["name"]
            form["party"] = party.ec_id
            form["source"] = context["official_document"].source_url
            initial.append(form)

        if self.request.POST:
            context["formset"] = forms.BulkAddReviewFormSet(
                self.request.POST,
                parties=context["parties"],
                ballot=context["post_election"],
            )
        else:
            context["formset"] = forms.BulkAddReviewFormSet(
                initial=initial,
                parties=context["parties"],
                ballot=context["post_election"],
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
                helpers.update_person(
                    self.request,
                    person,
                    Party.objects.get(
                        ec_id=person_form.cleaned_data["party"].split("__")[0]
                    ),
                    context["post_election"],
                    data["source"],
                )

            if self.request.POST.get("suggest_locking") == "on":
                pee = PostExtraElection.objects.get(
                    post=context["post"],
                    election=Election.objects.get(slug=context["election"]),
                )
                SuggestedPostLock.objects.create(
                    user=self.request.user, postextraelection=pee
                )

                LoggedAction.objects.create(
                    user=self.request.user,
                    action_type="suggest-ballot-lock",
                    ip_address=get_client_ip(self.request),
                    post_election=pee,
                    source="Suggested after bulk adding",
                )

                if hasattr(pee, "rawpeople"):
                    # Delete the raw import, as it's no longer useful
                    pee.rawpeople.delete()

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
            url = context["post_election"].get_absolute_url()
        return HttpResponseRedirect(url)

    def form_invalid(self, context):
        return self.render_to_response(context)
