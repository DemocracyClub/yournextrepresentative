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
            name = f"memberships_{membership.person.pk}"
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
                required=True,
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
        Returns tuple of membership field, and associated tied vote field. This
        allows us to loop through and render the fields next to each other in
        the template
        """
        for field in self.fields:
            if not field.startswith("memberships_"):
                continue

            tied_vote_field_name = f"tied_vote_{field}"
            yield (self[field], self[tied_vote_field_name])

    def clean(self):
        """
        Validates that there not more coin toss winners than seats up
        """
        cleaned_data = super().clean()

        if len(self._tied_vote_winners) > self.ballot.winner_count:
            raise forms.ValidationError(
                "Cant have more coin toss winners than seats up!"
            )

        return cleaned_data

    def save(self, request):
        with transaction.atomic():
            instance = super().save(commit=False)
            instance.ballot = self.ballot
            instance.user = (
                request.user if request.user.is_authenticated else None
            )
            instance.ip_address = get_client_ip(request)
            instance.save()

            winners = self.get_winners(num_winners=self.ballot.winner_count)
            self.ballot.membership_set.update(elected=None)

            recorder = RecordBallotResultsHelper(self.ballot, instance.user)
            for membership, field_name in self.memberships:
                tied_vote_winner = self.cleaned_data[f"tied_vote_{field_name}"]
                num_votes = self.cleaned_data[field_name]
                winner = field_name in winners
                instance.candidate_results.update_or_create(
                    membership=membership,
                    defaults={
                        "is_winner": winner,
                        "num_ballots": num_votes,
                        "tied_vote_winner": tied_vote_winner,
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

    @property
    def _tied_vote_winners(self):
        """
        Return a list of the tied vote fieldnames that won coin toss
        """
        return [
            field_name
            for field_name, value in self.cleaned_data.items()
            if field_name.startswith("tied_vote_") and value is True
        ]

    def get_winners(self, num_winners=1):
        """
        Return a dictionary of fieldname, num votes for each of candidates with
        the most votes.
        """
        results = {
            field: votes
            for field, votes in self.cleaned_data.items()
            if field.startswith("memberships_")
        }
        # builds a list of tuples made up of (fieldname, num votes)
        sorted_results = sorted(
            results.items(), reverse=True, key=lambda result: result[1]
        )
        winners = sorted_results[:num_winners]

        # can return sorted winners if there are no tied vote winners
        if not any(self._tied_vote_winners):
            return dict(sorted_results[:num_winners])

        # or we have ties so remove the winner with least votes
        lowest_winner = winners.pop()
        lowest_winner_votes = lowest_winner[1]

        winners = []
        tied_results = []
        # go back over the results and split to winners and tied results
        for result in sorted_results:
            if result[1] > lowest_winner_votes:
                winners.append(result)
                continue

            if result[1] == lowest_winner_votes:
                tied_results.append(result)

        # loop through tied results, and if they won a coin toss,
        # add them to the winners
        for result in tied_results:
            tied_field_name = f"tied_vote_{result[0]}"
            if tied_field_name in self._tied_vote_winners:
                winners.append(result)

        return dict(winners)
