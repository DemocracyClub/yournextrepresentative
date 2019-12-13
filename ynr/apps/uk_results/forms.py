from collections import OrderedDict

from django import forms
from django.db import transaction

from candidates.models import LoggedAction
from candidates.views.version_data import get_client_ip
from uk_results.helpers import RecordBallotResultsHelper
from utils.db import LastWord

from .models import ResultSet


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
                initial = membership.result.num_ballots
            except:
                initial = None
            fields[name] = forms.IntegerField(
                label="{} ({})".format(
                    membership.person.name, membership.party.name
                ),
                initial=initial,
                required=False,
            )
            self.memberships.append((membership, name))
        self.fields = fields
        self.fields.update(existing_fields)

    def membership_fields(self):
        return [
            self[field]
            for field in self.fields
            if field.startswith("memberships_")
        ]

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
                x.value() for x in self.membership_fields() if x.value()
            ]
            winners = {}
            if len(fields_with_values) == len(self.membership_fields()):
                winner_count = self.ballot.winner_count
                if winner_count:
                    winners = dict(
                        sorted(
                            [
                                (
                                    "{}-{}".format(
                                        self[y].value(), x.person.id
                                    ),
                                    x,
                                )
                                for x, y in self.memberships
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
