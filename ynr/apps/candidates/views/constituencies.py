from django.db import transaction
from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404
from django.views.generic import FormView, View

from auth_helpers.views import GroupRequiredMixin
from candidates.forms import ConstituencyRecordWinnerForm
from elections.mixins import ElectionMixin
from people.models import Person
from popolo.models import Post
from uk_results.helpers import RecordBallotResultsHelper

from ..models import RESULT_RECORDERS_GROUP_NAME, Ballot


class ConstituencyRecordWinnerView(ElectionMixin, GroupRequiredMixin, FormView):

    form_class = ConstituencyRecordWinnerForm
    template_name = "candidates/record-winner.html"
    required_group_name = RESULT_RECORDERS_GROUP_NAME

    def dispatch(self, request, *args, **kwargs):

        person_id = self.request.POST.get(
            "person_id", self.request.GET.get("person", "")
        )
        self.election_data = self.get_election()
        self.person = get_object_or_404(Person, id=person_id)
        self.post_data = get_object_or_404(Post, slug=self.kwargs["post_id"])
        self.ballot = Ballot.objects.get(
            election=self.election_data, post=self.post_data
        )
        return super().dispatch(request, *args, **kwargs)

    def get_initial(self):
        initial = super().get_initial()
        initial["person_id"] = self.person.id
        return initial

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["post_id"] = self.kwargs["post_id"]
        context["ballot"] = self.ballot
        context["constituency_name"] = self.post_data.label
        context["person"] = self.person
        return context

    def form_valid(self, form):
        with transaction.atomic():
            recorder = RecordBallotResultsHelper(self.ballot, self.request.user)
            recorder.mark_person_as_elected(
                self.person, form.cleaned_data["source"]
            )

        return HttpResponseRedirect(self.ballot.get_absolute_url())


class ConstituencyRetractWinnerView(ElectionMixin, GroupRequiredMixin, View):

    required_group_name = RESULT_RECORDERS_GROUP_NAME
    http_method_names = ["post"]

    def post(self, request, *args, **kwargs):
        self.post_data = get_object_or_404(Post, slug=self.kwargs["post_id"])
        self.ballot = Ballot.objects.get(
            election=self.election_data, post=self.post_data
        )

        with transaction.atomic():
            recorder = RecordBallotResultsHelper(self.ballot, self.request.user)
            recorder.retract_elected()

        return HttpResponseRedirect(self.ballot.get_absolute_url())
