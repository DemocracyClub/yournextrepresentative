from braces.views import LoginRequiredMixin
from django.db import transaction
from django.http import HttpResponseRedirect
from django.urls import reverse
from django.views.generic import FormView, TemplateView

from bulk_adding import forms, helpers
from elections.models import Election
from parties.models import Party
from people.models import Person
from popolo.models import Membership

# Assume 5 winners if we have no other info.
# If someone reports this, we can update EE and re-import
WINNER_COUNT_IF_NONE = 5


class BasePartyBulkAddView(LoginRequiredMixin, TemplateView):
    def get_election(self):
        if not hasattr(self, "_election_obj"):
            self._election_obj = Election.objects.get(
                slug=self.kwargs["election"]
            )
        return self._election_obj

    def get_party(self):
        return Party.objects.get(ec_id=self.kwargs["party_id"])

    def get_ballot_qs(self, election):
        qs = election.ballot_set.all()
        qs = qs.order_by("post__label")
        return qs


class SelectPartyForm(BasePartyBulkAddView, FormView):
    template_name = "bulk_add/parties/select_party.html"
    form_class = forms.SelectPartyForm

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["election_obj"] = self.get_election()
        return context

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["election"] = self.get_election()
        return kwargs

    def form_invalid(self, form):
        form_data = dict(form.data)
        for k in list(form_data):
            if not k == "csrfmiddlewaretoken":
                del form_data[k]
            form.data = form_data
        return self.render_to_response(self.get_context_data(form=form))

    def form_valid(self, form):
        return HttpResponseRedirect(
            reverse(
                "bulk_add_by_party",
                kwargs={
                    "election": self.get_election().slug,
                    "party_id": form.cleaned_data["party"]["party_id"],
                },
            )
        )


class BulkAddPartyView(BasePartyBulkAddView):
    template_name = "bulk_add/parties/add_form.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["election_obj"] = self.get_election()
        context["party"] = self.get_party()
        context["form"] = kwargs.get(
            "form", forms.AddByPartyForm(self.request.POST)
        )
        posts = []
        qs = self.get_ballot_qs(context["election_obj"])
        for ballot in qs:
            existing = Membership.objects.filter(
                ballot__election=ballot.election,
                post=ballot.post,
                party=context["party"],
            )
            extra_forms = ballot.winner_count or WINNER_COUNT_IF_NONE
            form_kwargs = {"ballot": ballot}
            if self.request.POST:
                formset = forms.BulkAddByPartyFormset(
                    self.request.POST, **form_kwargs
                )
            else:
                formset = forms.BulkAddByPartyFormset(**form_kwargs)

            post_info = {
                "ballot": ballot,
                "existing": existing,
                "formset": formset,
            }
            posts.append(post_info)

        context["posts"] = posts

        return context

    def post(self, *args, **kwargs):
        qs = self.get_ballot_qs(self.get_election())
        form = forms.AddByPartyForm(self.request.POST)

        has_some_data = any(
            [v for k, v in self.request.POST.items() if k.endswith("-name")]
        )
        if not has_some_data:
            form.add_error(None, "Please enter at least one name")

        if not has_some_data or not form.is_valid():
            return self.render_to_response(self.get_context_data(form=form))

        session_data = {"source": form.cleaned_data["source"], "post_data": []}
        for ballot in qs:
            form_kwargs = {"ballot": ballot}
            formset = forms.BulkAddByPartyFormset(
                self.request.POST, **form_kwargs
            )

            session_data["post_data"].append(
                {"ballot_pk": ballot.pk, "data": formset.cleaned_data}
            )
        self.request.session["bulk_add_by_party_data"] = session_data
        self.request.session.save()

        return HttpResponseRedirect(
            reverse(
                "bulk_add_by_party_review",
                kwargs={
                    "election": self.kwargs["election"],
                    "party_id": self.kwargs["party_id"],
                },
            )
        )


class BulkAddPartyReviewView(BasePartyBulkAddView):
    template_name = "bulk_add/parties/add_review_form.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        post_data = self.request.session["bulk_add_by_party_data"].get(
            "post_data"
        )
        election = self.get_election()
        party = self.get_party()
        formsets = []
        for post in post_data:
            if not any(post["data"]):
                # This post election might not have any names, that's ok.
                continue

            ballot = election.ballot_set.get(pk=post["ballot_pk"])

            if self.request.POST:
                formset = forms.PartyBulkAddReviewNameOnlyFormSet(
                    self.request.POST,
                    initial=post["data"],
                    prefix=ballot.pk,
                    ballot=ballot,
                )
            else:
                formset = forms.PartyBulkAddReviewNameOnlyFormSet(
                    initial=post["data"], prefix=ballot.pk, ballot=ballot
                )
            formsets.append(
                {
                    "ballot": ballot,
                    "data": formset,
                    "management_form": formset.management_form,
                }
            )

        context["formsets"] = formsets
        context["election_obj"] = election
        context["party"] = party
        return context

    def post(self, request, *args, **kwargs):
        qs = self.get_ballot_qs(self.get_election())
        formsets = []
        ballot_ids = {
            int(k.split("-")[0])
            for k in request.POST.keys()
            if k.endswith("-name")
        }
        for ballot in qs.filter(pk__in=ballot_ids):
            formset = forms.PartyBulkAddReviewNameOnlyFormSet(
                self.request.POST, prefix=ballot.pk, ballot=ballot
            )

            formsets.append(formset)

        if all([f.is_valid() for f in formsets]):
            return self.form_valid(formsets)
        else:
            return self.form_invalid()

    def form_valid(self, formsets):

        source = self.request.session["bulk_add_by_party_data"].get("source")
        assert len(formsets) >= 1

        with transaction.atomic():
            for formset in formsets:
                for person_form in formset:
                    data = person_form.cleaned_data

                    # Ignore blank extra forms with no name
                    # This happens when we have fewer names
                    # than the winner_count for this ballot
                    if not data.get("select_person"):
                        continue

                    data["source"] = source
                    if data.get("select_person") == "_new":
                        # Add a new person
                        person = helpers.add_person(self.request, data)
                    else:
                        person = Person.objects.get(
                            pk=int(data["select_person"])
                        )

                    # TODO check about updating PartyDescription here
                    # Update the person's candacies
                    helpers.update_person(
                        self.request,
                        person,
                        self.get_party(),
                        formset.ballot,
                        source,
                        list_position=data.get("party_list_position"),
                    )

        url = self.get_election().get_absolute_url()
        return HttpResponseRedirect(url)

    def form_invalid(self):
        context = self.get_context_data()
        return self.render_to_response(context)
