from collections import Counter
from typing import Dict

from bulk_adding import forms, helpers
from bulk_adding.forms import QuickAddSinglePersonForm
from bulk_adding.models import RawPeople
from candidates.models import Ballot, LoggedAction, raise_if_unsafe_to_delete
from candidates.models.db import ActionType, EditType
from candidates.views.version_data import get_client_ip
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db import transaction
from django.db.models import Count, F, Prefetch
from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404
from django.urls import reverse
from django.views.generic import FormView, RedirectView, TemplateView
from moderation_queue.models import SuggestedPostLock
from official_documents.models import BallotSOPN
from official_documents.views import get_add_from_document_cta_flash_message
from parties.models import Party, PartyDescription
from people.models import Person
from popolo.models import Membership


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
        if hasattr(self, "ballot"):
            return self.ballot
        queryset = Ballot.objects.select_related(
            "post", "election", "rawpeople", "post__party_set", "sopn"
        ).annotate(membership_count=Count("membership"))
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
            context["ballot_sopn"] = self.ballot.sopn
        except BallotSOPN.DoesNotExist:
            context["ballot_sopn"] = None
        self.ballot_sopn = context["ballot_sopn"]
        return context

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(self.add_election_and_post_to_context(context))
        return context

    def remaining_posts_for_sopn(self):
        # TODO: Use ElectionSOPN?
        return BallotSOPN.objects.filter(
            source_url=self.ballot_sopn.source_url,
            ballot__election=F("ballot__election"),
            ballot__suggestedpostlock=None,
        )

    def post(self, request, *args, **kwargs):
        context = self.get_context_data(**kwargs)
        if context["formset"].is_valid():
            return self.form_valid(context)
        return self.form_invalid(context)


class BulkAddSOPNView(BaseSOPNBulkAddView):
    template_name = "bulk_add/sopns/add_form.html"

    def get(self, request, *args, **kwargs):
        self.ballot = self.get_ballot()
        if not request.GET.get("edit") and (
            hasattr(self.ballot, "rawpeople")
            and self.ballot.rawpeople.is_trusted
            and self.ballot.rawpeople.textract_data
        ):
            return HttpResponseRedirect(
                self.ballot.get_bulk_add_reconcile_url()
            )
        if not hasattr(self.ballot, "rawpeople"):
            self.ballot.rawpeople = RawPeople.objects.create(ballot=self.ballot)

        self.ballot.rawpeople.claim(self.request.user)
        return super().get(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        form_kwargs = {"ballot": context["ballot"]}

        if hasattr(context["ballot"], "rawpeople"):
            rawpeople = context["ballot"].rawpeople
            form_kwargs.update(rawpeople.as_form_kwargs())
            context["has_parsed_people"] = rawpeople.source_type == "parsed_pdf"
            if rawpeople.is_claimed_by_another_user(self.request.user):
                context["bulk_add_claim_warning"] = rawpeople.claimed_by
                context["bulk_add_claimed_at"] = rawpeople.claimed_at

        if "ballot_sopn" in context and context["ballot_sopn"] is not None:
            form_kwargs["source"] = context["ballot_sopn"].source_url

        if self.request.POST:
            context["formset"] = forms.BulkAddFormSetFactory(
                self.request.POST, **form_kwargs
            )
        else:
            context["formset"] = forms.BulkAddFormSetFactory(**form_kwargs)

        return context

    def form_valid(self, context):
        raw_ballot_data = []
        for form_data in context["formset"].cleaned_data:
            if not form_data or form_data.get("DELETE"):
                continue
            party_id = form_data["party"]["party_id"]
            candidate_data = {
                "name": form_data["name"],
                "sopn_last_name": form_data["sopn_last_name"],
                "sopn_first_names": form_data["sopn_first_names"],
                "party_id": party_id,
                "description_id": form_data["party"]["description_id"],
            }
            if form_data["previous_party_affiliations"]:
                candidate_data["previous_party_affiliations"] = form_data[
                    "previous_party_affiliations"
                ]
            if form_data.get("party_list_position") is not None:
                candidate_data["party_list_position"] = form_data[
                    "party_list_position"
                ]

            raw_ballot_data.append(candidate_data)

        raw_people, _ = RawPeople.objects.update_or_create(
            ballot=context["ballot"],
            defaults={
                "textract_data": raw_ballot_data,
                "source": context["ballot_sopn"].source_url[:512],
                "source_type": RawPeople.SOURCE_BULK_ADD_FORM,
                # Blank out the reconciled_data if we're submitting a new form
                "reconciled_data": {},
            },
        )
        raw_people.claim(self.request.user)

        return HttpResponseRedirect(
            context["ballot"].get_bulk_add_reconcile_url()
        )

    def form_invalid(self, context):
        return self.render_to_response(context)


class BulkAddSOPNReconcileView(BaseSOPNBulkAddView):
    template_name = "bulk_add/sopns/add_reconcile_form.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        initial = []

        if hasattr(self.ballot, "rawpeople"):
            raw_ballot_data = self.ballot.rawpeople.textract_data
            if self.ballot.rawpeople.reconciled_data:
                raw_ballot_data = self.ballot.rawpeople.reconciled_data
        else:
            # Race condition! Someone else has processes this area
            # between page views. Best just show the data we have.
            raw_ballot_data = []

        parties = Party.objects.prefetch_related(
            Prefetch(
                "descriptions",
                PartyDescription.objects.all(),
            )
        ).filter(
            ec_id__in=[candidacy["party_id"] for candidacy in raw_ballot_data]
        )
        parties_dict = {}
        for party in parties:
            descriptions = {desc.pk: desc for desc in party.descriptions.all()}
            parties_dict[party.ec_id] = {
                "party": party,
                "descriptions": descriptions,
            }
        for candidacy in raw_ballot_data:
            form = {}
            party_dict = parties_dict[candidacy["party_id"]]
            party_obj = party_dict["party"]

            form["party_description_text"] = party_obj.name
            description_pk = candidacy.get("description_id")
            if description_pk:
                party_description = party_dict["descriptions"].get(
                    description_pk
                )
                if party_description:
                    form["description_id"] = party_description
                    form[
                        "party_description_text"
                    ] = party_description.description

            form["name"] = candidacy["name"]
            form["party_id"] = party_obj.ec_id
            form["source"] = context["ballot_sopn"].source_url
            form["sopn_last_name"] = candidacy["sopn_last_name"]
            form["sopn_first_names"] = candidacy["sopn_first_names"]

            if candidacy.get("previous_party_affiliations"):
                form["previous_party_affiliations"] = ",".join(
                    candidacy["previous_party_affiliations"]
                )

            if candidacy.get("party_list_position") is not None:
                form["party_list_position"] = candidacy["party_list_position"]

            # Restore the user's previous select_person choice when navigating
            # back from the confirm page
            if candidacy.get("select_person"):
                form["select_person"] = candidacy["select_person"]

            initial.append(form)

        if self.request.POST:
            context["formset"] = forms.BulkAddReconcileFormSet(
                self.request.POST, ballot=context["ballot"]
            )
        else:
            context["formset"] = forms.BulkAddReconcileFormSet(
                initial=initial, ballot=context["ballot"]
            )
        return context

    def form_valid(self, context):
        ballot = context["ballot"]
        rawpeople: RawPeople = getattr(ballot, "rawpeople", None)
        if not rawpeople:
            # We end up in this situation when someone else has bulk added
            # and suggested locking. There's not much we can do here
            # so we can redirect to the ballot page where the user
            # will at least get a message about the state of the ballot
            return HttpResponseRedirect(ballot.get_absolute_url())

        # Save this form to the reconciled_data field of the rawpeople object
        reconciled_data = []
        for person_form in context["formset"]:
            # Replace the description_id object with its pk for JSON storage.
            form_data = dict(person_form.cleaned_data)
            if form_data["description_id"]:
                form_data["description_id"] = form_data["description_id"].pk
            reconciled_data.append(form_data)
        rawpeople.reconciled_data = reconciled_data
        rawpeople.save()
        url = reverse(
            "bulk_add_sopn_confirm",
            kwargs={"ballot_paper_id": ballot.ballot_paper_id},
        )
        return HttpResponseRedirect(url)

    def form_invalid(self, context):
        return self.render_to_response(context)


class BulkAddSOPNConfirmView(BaseSOPNBulkAddView):
    template_name = "bulk_add/sopns/add_confirm.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Get existing people on the ballot that we'll be removing
        reconciled_data = {
            person["select_person"]
            for person in context["ballot"].rawpeople.reconciled_data
            if person["select_person"] != "_new"
        }
        people_on_ballot = {
            mem["person_id"]
            for mem in context["ballot"]
            .membership_set.all()
            .values("person_id")
        }
        candidacies_to_remove = people_on_ballot - reconciled_data
        context["candidacies_to_remove"] = Membership.objects.filter(
            person_id__in=candidacies_to_remove, ballot=self.ballot
        ).select_related("person", "party")

        context["contested_warnings"] = self.odd_candidate_count_warnings(
            context["ballot"], context["ballot"].rawpeople.reconciled_data
        )

        return context

    def odd_candidate_count_warnings(
        self, ballot, reconciled_data
    ) -> Dict[str, Dict]:
        """
        Returns parties that are over- or under-contested.

        Output format:
        {
            "over": {"PP52": {"count": 3, "party: <Party>}, ...},
            "under": {"PP53": 1, "party: <Party>, ...},
        }
        """
        # Count candidates per party
        party_model_cache = {
            party.ec_id: party
            for party in Party.objects.filter(
                ec_id__in=[
                    c["party_id"] for c in reconciled_data if c.get("party_id")
                ]
            )
        }
        counts = Counter(
            c["party_id"] for c in reconciled_data if c.get("party_id")
        )

        over = {}
        under = {}

        for party, count in counts.items():
            if count != ballot.winner_count:
                party_obj: Party = party_model_cache[party]
                if count > ballot.winner_count:
                    over[party] = {"count": count, "party": party_obj}
                elif count < ballot.winner_count:
                    under[party] = {"count": count, "party": party_obj}

        return {
            "over": over,
            "under": under,
        }

    def post(self, request, *args, **kwargs):
        context = self.get_context_data(**kwargs)
        ballot = context["ballot"]
        rawpeople = getattr(ballot, "rawpeople", None)
        if not rawpeople or not rawpeople.reconciled_data:
            return HttpResponseRedirect(ballot.get_bulk_add_reconcile_url())
        return self.form_valid(context)

    def form_valid(self, context):
        ballot = context["ballot"]
        rawpeople: RawPeople = getattr(ballot, "rawpeople", None)
        with transaction.atomic():
            for person_data in rawpeople.reconciled_data:
                if person_data.get("select_person") == "_new":
                    # Add a new person
                    person = helpers.add_person(self.request, person_data)
                else:
                    person = Person.objects.get(
                        pk=int(person_data["select_person"])
                    )
                party = Party.objects.get(ec_id=person_data["party_id"])
                previous_party_affiliations = person_data.get(
                    "previous_party_affiliations", None
                )
                if previous_party_affiliations:
                    party_ids = person_data[
                        "previous_party_affiliations"
                    ].split(",")
                    previous_party_affiliations = Party.objects.filter(
                        ec_id__in=party_ids
                    )

                helpers.update_person(
                    request=self.request,
                    person=person,
                    party=party,
                    ballot=context["ballot"],
                    source=person_data["source"],
                    party_description=person_data["description_id"],
                    list_position=person_data.get("party_list_position"),
                    previous_party_affiliations=previous_party_affiliations,
                    sopn_last_name=person_data["sopn_last_name"],
                    sopn_first_names=person_data["sopn_first_names"],
                    data=person_data,
                )

            # ballot has changed so we should remove any out of date suggestions
            ballot = context["ballot"]
            ballot.delete_outdated_suggested_locks()

            SuggestedPostLock.objects.create(
                user=self.request.user, ballot=ballot
            )

            # Remove people on the ballot but not matched
            for candidacy in context["candidacies_to_remove"]:
                LoggedAction.objects.create(
                    user=self.request.user,
                    action_type=ActionType.CANDIDACY_DELETE,
                    ip_address=get_client_ip(self.request),
                    ballot=ballot,
                    source="Removed from ballot as not listed on SOPN",
                    edit_type=EditType.BULK_ADD.name,
                )
                raise_if_unsafe_to_delete(candidacy)
                candidacy.delete()

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
                self.ballot_sopn, self.remaining_posts_for_sopn()
            ),
            extra_tags="safe do-something-else",
        )

        remaining_qs = self.remaining_posts_for_sopn().exclude(
            pk=self.ballot_sopn.pk
        )
        if remaining_qs.exists():
            url = reverse(
                "posts_for_document", kwargs={"pk": self.ballot_sopn.pk}
            )
        else:
            url = context["ballot"].get_absolute_url()
        return HttpResponseRedirect(url)


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
