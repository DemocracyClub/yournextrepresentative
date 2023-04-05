from braces.views import LoginRequiredMixin
from django.contrib import messages
from django.db import transaction
from django.db.models import F
from django.db.models.query import Prefetch
from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404
from django.urls import reverse
from django.views.generic import RedirectView, TemplateView, FormView

from bulk_adding import forms, helpers
from bulk_adding.forms import QuickAddSinglePersonForm
from bulk_adding.models import RawPeople
from candidates.models import Ballot, LoggedAction
from candidates.models.db import EditType, ActionType
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


def sort_tables(key):
    if isinstance(key, QuickAddSinglePersonForm):
        name = key.initial.get("name", None)
        value = "zzzzzzzzzz"
        if name:
            value = name.split(" ")[-1]
    if isinstance(key, Person):
        value = key.last_name_guess
    return (value is not None, value)


class BaseSOPNBulkAddView(LoginRequiredMixin, TemplateView):
    def get_ballot(self):
        """
        Get the ballot object with related objects prefetched where possible to
        help performance.
        """
        queryset = Ballot.objects.select_related(
            "post", "election", "rawpeople", "post__party_set"
        ).prefetch_related(
            "membership_set",
            "membership_set__person",
            "membership_set__person__other_names",
            "membership_set__party",
            "membership_set__party__descriptions",
            Prefetch(
                "officialdocument_set",
                queryset=OfficialDocument.objects.filter(
                    document_type=OfficialDocument.NOMINATION_PAPER
                ),
            ),
        )
        return get_object_or_404(
            queryset, ballot_paper_id=self.kwargs["ballot_paper_id"]
        )

    def add_election_and_post_to_context(self, context):
        if not hasattr(self, "ballot"):
            self.ballot = self.get_ballot()
        context["ballot"] = self.ballot
        context["post"] = self.ballot.post
        context["election_obj"] = self.ballot.election
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
            person.previous_party_affiliations = (
                membership.previous_party_affiliations.all()
            )

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
            self.ballot = self.get_ballot()
            if hasattr(self.ballot, "rawpeople"):
                if self.ballot.rawpeople.is_trusted:
                    return HttpResponseRedirect(
                        self.ballot.get_bulk_add_review_url()
                    )
        return super().get(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        form_kwargs = {"ballot": context["ballot"]}

        if hasattr(context["ballot"], "rawpeople"):
            form_kwargs.update(context["ballot"].rawpeople.as_form_kwargs())
            context["has_parsed_people"] = (
                context["ballot"].rawpeople.source_type == "parsed_pdf"
            )

        if (
            "official_document" in context
            and context["official_document"] is not None
        ):
            form_kwargs["source"] = context["official_document"].source_url

        if self.request.POST:
            context["formset"] = forms.BulkAddFormSetFactory(
                self.request.POST, **form_kwargs
            )
        else:
            context["formset"] = forms.BulkAddFormSetFactory(**form_kwargs)

        tables = list(context["formset"]) + context["known_people"]
        sorted_tables = sorted(tables, key=sort_tables, reverse=False)
        sorted_with_type = []
        for table in sorted_tables:
            if isinstance(table, QuickAddSinglePersonForm):
                row = {
                    "template_name": "bulk_add/sopns/quick_add_form.html",
                    "data": table,
                }
            if isinstance(table, Person):
                row = {
                    "template_name": "bulk_add/sopns/existing_person_table.html",
                    "data": table,
                }
            sorted_with_type.append(row)
        context["sorted_with_type"] = sorted_with_type

        return context

    def form_valid(self, context):
        raw_ballot_data = []
        for form_data in context["formset"].cleaned_data:
            if not form_data or form_data.get("DELETE"):
                continue
            party_id = form_data["party"]["party_id"]
            description_id = form_data["party"]["description_id"]
            candidate_data = {
                "name": form_data["name"],
                "party_id": party_id,
                "description_id": description_id,
            }
            if form_data["previous_party_affiliations"]:
                candidate_data["previous_party_affiliations"] = form_data[
                    "previous_party_affiliations"
                ]

            raw_ballot_data.append(candidate_data)

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

            if candidacy.get("previous_party_affiliations"):
                form["previous_party_affiliations"] = ",".join(
                    candidacy["previous_party_affiliations"]
                )

            initial.append(form)

        if self.request.POST:
            context["formset"] = forms.BulkAddReviewFormSet(
                self.request.POST, ballot=context["ballot"]
            )
        else:
            context["formset"] = forms.BulkAddReviewFormSet(
                initial=initial, ballot=context["ballot"]
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
                previous_party_affiliations = data.get(
                    "previous_party_affiliations", None
                )
                if previous_party_affiliations:
                    party_ids = data["previous_party_affiliations"].split(",")
                    previous_party_affiliations = Party.objects.filter(
                        ec_id__in=party_ids
                    )

                helpers.update_person(
                    request=self.request,
                    person=person,
                    party=party,
                    ballot=context["ballot"],
                    source=data["source"],
                    party_description=data["party_description"],
                    previous_party_affiliations=previous_party_affiliations,
                )

            # ballot has changed so we should remove any out of date suggestions
            ballot = context["ballot"]
            ballot.delete_outdated_suggested_locks()

            SuggestedPostLock.objects.create(
                user=self.request.user, ballot=ballot
            )

            LoggedAction.objects.create(
                user=self.request.user,
                action_type=ActionType.SUGGEST_BALLOT_LOCK,
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


class DeleteRawPeople(LoginRequiredMixin, FormView):
    """
    View to delete a RawPeople object for a ballot
    """

    form_class = forms.DeleteRawPeopleForm

    def form_valid(self, form):
        ballot = get_object_or_404(
            Ballot, ballot_paper_id=form.cleaned_data["ballot_paper_id"]
        )
        try:
            ballot.rawpeople.delete()
            LoggedAction.objects.create(
                user=self.request.user,
                ip_address=get_client_ip(self.request),
                action_type=ActionType.DELETED_PARSED_RAW_PEOPLE,
                ballot=ballot,
                edit_type=EditType.USER.name,
            )
        except RawPeople.DoesNotExist:
            pass

        return HttpResponseRedirect(ballot.get_bulk_add_url())
