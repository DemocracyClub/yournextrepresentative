from collections import OrderedDict

from django import forms
from django.db import transaction

from candidates.models import LoggedAction
from candidates.views.version_data import get_client_ip
from uk_results.helpers import RecordBallotResultsHelper
from utils.db import LastWord

from .models import CandidateResult, ResultSet


class ResultSetForm(forms.ModelForm):
    class Meta:
        model = ResultSet
        fields = ("num_turnout_reported", "num_spoilt_ballots", "source")
        widgets = {"source": forms.Textarea(attrs={"rows": 1, "columns": 72})}

    def __init__(self, ballot, *args, **kwargs):
        self.ballot = ballot
        self.memberships = []

        super().__init__(*args, **kwargs)

        self.fields["num_spoilt_ballots"].required = False
        self.fields["num_spoilt_ballots"].label += " (Not required)"
        self.fields["num_turnout_reported"].required = False
        self.fields["num_turnout_reported"].label += " (Percent, not required)"

        existing_fields = self.fields
        fields = OrderedDict()
        memberships = (
            ballot.membership_set.all()
            .annotate(sorted_name=LastWord("person__name"))
            .order_by("sorted_name")
        )

        for membership in memberships:
            name = "memberships_%d" % membership.person.pk
            try:
                initial = {
                    "num_ballots": membership.result.num_ballots,
                    "tied_vote_winner": membership.result.tied_vote_winner,
                }
            except CandidateResult.DoesNotExist:
                initial = {}

            fields[name] = forms.IntegerField(
                label=membership.name_and_party,
                initial=initial.get("num_ballots"),
                required=False,
            )
            fields[f"tied_vote_{name}"] = forms.BooleanField(
                required=False,
                label="Coin toss winner?",
                initial=initial.get("tied_vote_winner"),
            )
            self.memberships.append((membership, name))

        self.fields = fields
        self.fields.update(existing_fields)

    def membership_fields(self):
        """
        Returns tuple of membership field, and associated tied vote field
        """
        for field in self.fields:
            if not field.startswith("memberships_"):
                continue

            tied_vote_field_name = f"tied_vote_{field}"
            yield (self[field], self[tied_vote_field_name])

    def save(self, request):
        with transaction.atomic():
            instance = super().save(commit=False)
            instance.ballot = self.ballot
            instance.user = (
                request.user if request.user.is_authenticated else None
            )
            instance.ip_address = get_client_ip(request)
            instance.save()

            fields_with_values = [
                membership_field.value()
                for membership_field, _ in self.membership_fields()
                if membership_field.value()
            ]
            winners = {}
            if len(fields_with_values) == len(list(self.membership_fields())):
                winner_count = self.ballot.winner_count
                if winner_count:
                    winners = dict(
                        sorted(
                            [
                                (
                                    "{}-{}".format(
                                        self[field_name].value(), obj.person.id
                                    ),
                                    obj,
                                )
                                for obj, field_name in self.memberships
                            ],
                            reverse=True,
                            key=lambda votes: int(votes[0].split("-")[0]),
                        )[:winner_count]
                    )
                else:
                    winners = {}

            if winners:
                self.ballot.membership_set.update(elected=None)
            recorder = RecordBallotResultsHelper(self.ballot, instance.user)
            for membership, field_name in self.memberships:
                if not self[field_name].value():
                    continue
                winner = bool(membership in winners.values())
                instance.candidate_results.update_or_create(
                    membership=membership,
                    defaults={
                        "is_winner": winner,
                        "num_ballots": self[field_name].value(),
                        "tied_vote_winner": self[
                            f"tied_vote_{field_name}"
                        ].value(),
                    },
                )
                if winner:
                    recorder.mark_person_as_elected(
                        membership.person, source=instance.source
                    )

            instance.record_version()

            LoggedAction.objects.create(
                user=instance.user,
                action_type="entered-results-data",
                source=instance.source,
                ballot=instance.ballot,
            )

        return instance
