from braces.views import LoginRequiredMixin
from django.contrib import messages
from django.core.urlresolvers import reverse
from django.db import transaction
from django.db.models import F
from django.http import HttpResponseRedirect
from django.utils.text import slugify
from django.views.generic import RedirectView, TemplateView
from popolo.models import Organization, Person, Post

from bulk_adding import forms, helpers
from candidates.models import PostExtraElection
from elections.models import Election
from moderation_queue.models import SuggestedPostLock
from official_documents.models import OfficialDocument
from official_documents.views import get_add_from_document_cta_flash_message


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
        context["parties"] = context["post"].party_set.party_choices(**kwargs)
        context["official_document"] = OfficialDocument.objects.filter(
            post__slug=context["post_id"], election__slug=context["election"]
        ).first()
        self.official_document = context["official_document"]
        return context

    def remaining_posts_for_sopn(self):
        return OfficialDocument.objects.filter(
            source_url=self.official_document.source_url,
            post__postextraelection__election=F("election"),
            post__postextraelection__suggestedpostlock=None,
        )

    def post(self, request, *args, **kwargs):
        context = self.get_context_data(**kwargs)
        if context["formset"].is_valid():
            return self.form_valid(context)
        else:
            return self.form_invalid(context)


class BulkAddSOPNView(BaseSOPNBulkAddView):
    template_name = "bulk_add/sopns/add_form.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(self.add_election_and_post_to_context(context))

        form_kwargs = {
            "parties": context["parties"],
            "party_set": context["post"].party_set,
        }

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

        people_set = set()
        for membership in context["post"].memberships.filter(
            post_election__election=context["election_obj"]
        ):
            person = membership.person
            person.party = membership.on_behalf_of
            people_set.add(person)

        known_people = list(people_set)
        known_people.sort(key=lambda i: i.name.split(" ")[-1])
        context["known_people"] = known_people

        return context

    def form_valid(self, context):
        self.request.session["bulk_add_data"] = context["formset"].cleaned_data
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
        context.update(self.add_election_and_post_to_context(context))

        initial = []

        for form in self.request.session["bulk_add_data"]:
            if form:
                if "__" in form["party"]:
                    org_id, other_name_id = form["party"].split("__")
                    org = Organization.objects.get(pk=org_id)
                    desc = org.other_names.get(pk=other_name_id)
                else:
                    desc = Organization.objects.get(pk=form["party"]).name

                form["party_description"] = desc
                initial.append(form)

        if self.request.POST:
            context["formset"] = forms.BulkAddReviewFormSet(
                self.request.POST, parties=context["parties"]
            )
        else:
            context["formset"] = forms.BulkAddReviewFormSet(
                initial=initial, parties=context["parties"]
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
                    Organization.objects.get(
                        pk=person_form.cleaned_data["party"].split("__")[0]
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

        messages.add_message(
            self.request,
            messages.SUCCESS,
            get_add_from_document_cta_flash_message(
                self.official_document, self.remaining_posts_for_sopn()
            ),
            extra_tags="safe do-something-else",
        )

        if self.remaining_posts_for_sopn().exists():
            url = reverse(
                "posts_for_document", kwargs={"pk": self.official_document.pk}
            )
        else:
            url = reverse(
                "constituency",
                kwargs={
                    "election": context["election"],
                    "post_id": context["post"].slug,
                    "ignored_slug": slugify(context["post"].label),
                },
            )
        return HttpResponseRedirect(url)

    def form_invalid(self, context):
        return self.render_to_response(context)
