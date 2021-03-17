from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import Group
from django.db import transaction
from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404, render
from django.utils.decorators import method_decorator
from django.views.generic import FormView, View

from candidates.forms import ConstituencyRecordWinnerForm
from elections.mixins import ElectionMixin
from people.models import Person
from uk_results.helpers import RecordBallotResultsHelper

from ..models import RESULT_RECORDERS_GROUP_NAME


class CanRecordResultsMixin:
    permission_denied_template = "auth_helpers/group_permission_denied.html"

    @method_decorator(login_required)
    def dispatch(self, request, *args, **kwargs):
        if not self.can_record_results():
            return render(request, self.permission_denied_template, status=403)
        return super().dispatch(request, *args, **kwargs)

    def can_record_results(self):
        if getattr(settings, "ALWAYS_ALLOW_RESULT_RECORDING", False):
            return True
        group = Group.objects.get(name=RESULT_RECORDERS_GROUP_NAME)
        return group in self.request.user.groups.all()


class ConstituencyRecordWinnerView(
    ElectionMixin, CanRecordResultsMixin, FormView
):

    form_class = ConstituencyRecordWinnerForm
    template_name = "candidates/record-winner.html"

    def dispatch(self, request, *args, **kwargs):

        person_id = self.request.POST.get("person_id")
        self.ballot = self.get_ballot()
        self.person = get_object_or_404(Person, id=person_id)
        return super().dispatch(request, *args, **kwargs)

    def get_initial(self):
        initial = super().get_initial()
        initial["person_id"] = self.person.id
        return initial

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["post_id"] = self.ballot.post.slug
        context["ballot"] = self.ballot
        context["winner_logged_action"] = self.ballot.loggedaction_set.filter(
            action_type="set-candidate-elected"
        ).order_by("-created")
        context["constituency_name"] = self.ballot.post.label
        context["person"] = self.person
        return context

    def form_valid(self, form):
        all_winners_set = (
            self.ballot.membership_set.filter(elected=True).count()
            >= self.ballot.get_winner_count
        )
        if all_winners_set:
            form.add_error(
                None,
                "All the winners for this ballot have been set."
                "If there is an error, you should unset them and reset the correct winner(s)",
            )
            return self.form_invalid(form)
        with transaction.atomic():
            recorder = RecordBallotResultsHelper(self.ballot, self.request.user)
            recorder.mark_person_as_elected(
                self.person, form.cleaned_data["source"]
            )

        return HttpResponseRedirect(self.ballot.get_absolute_url())


class ConstituencyRetractWinnerView(ElectionMixin, CanRecordResultsMixin, View):

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
