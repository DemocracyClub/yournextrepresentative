from collections import OrderedDict

from django import forms
from django.db import transaction

from candidates.models import LoggedAction
from candidates.views.version_data import get_change_metadata, get_client_ip
from results.models import ResultEvent

from .models import ResultSet


def mark_candidates_as_winner(request, instance):
    for candidate_result in instance.candidate_results.all():
        membership = candidate_result.membership
        post_election = instance.post_election
        election = post_election.election

        source = instance.source

        change_metadata = get_change_metadata(request, source)

        if candidate_result.is_winner:
            membership.elected = True
            membership.save()

            ResultEvent.objects.create(
                election=election,
                winner=membership.person,
                post=post_election.post,
                old_post_id=post_election.post.slug,
                old_post_name=post_election.post.label,
                winner_party=membership.party,
                source=source,
                user=request.user,
            )

            membership.person.record_version(change_metadata)
            membership.person.save()

            LoggedAction.objects.create(
                user=instance.user,
                action_type="set-candidate-elected",
                popit_person_new_version=change_metadata["version_id"],
                person=membership.person,
                source=source,
            )
        else:
            change_metadata[
                "information_source"
            ] = 'Setting as "not elected" by implication'
            membership.person.record_version(change_metadata)
            membership.elected = False
            membership.save()


class ResultSetForm(forms.ModelForm):
    class Meta:
        model = ResultSet
        fields = ("num_turnout_reported", "num_spoilt_ballots", "source")
        widgets = {"source": forms.Textarea(attrs={"rows": 1, "columns": 72})}

    def __init__(self, post_election, *args, **kwargs):
        self.post_election = post_election
        self.memberships = []

        super().__init__(*args, **kwargs)

        self.fields["num_spoilt_ballots"].required = False
        self.fields["num_spoilt_ballots"].label += " (Not required)"
        self.fields["num_turnout_reported"].required = False
        self.fields["num_turnout_reported"].label += " (Percent, not required)"

        existing_fields = self.fields
        fields = OrderedDict()
        memberships = post_election.membership_set.all()
        memberships = sorted(
            memberships, key=lambda member: member.person.name.split(" ")[-1]
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
            )
            self.memberships.append((membership, name))
        self.fields = fields
        self.fields.update(existing_fields)

    def membership_fields(self):
        return [
            field for field in self if field.name.startswith("memberships_")
        ]

    def save(self, request):
        with transaction.atomic():
            instance = super().save(commit=False)
            instance.post_election = self.post_election
            instance.user = (
                request.user if request.user.is_authenticated else None
            )
            instance.ip_address = get_client_ip(request)
            instance.save()

            winner_count = self.post_election.winner_count
            if winner_count:
                winners = dict(
                    sorted(
                        [
                            ("{}-{}".format(self[y].value(), x.person.id), x)
                            for x, y in self.memberships
                        ],
                        reverse=True,
                        key=lambda votes: int(votes[0].split("-")[0]),
                    )[:winner_count]
                )
            else:
                winners = {}

            for membership, field_name in self.memberships:
                instance.candidate_results.update_or_create(
                    membership=membership,
                    defaults={
                        "is_winner": bool(membership in winners.values()),
                        "num_ballots": self[field_name].value(),
                    },
                )

            mark_candidates_as_winner(request, instance)
            instance.record_version()

            LoggedAction.objects.create(
                user=instance.user,
                action_type="entered-results-data",
                source=instance.source,
                post_election=instance.post_election,
            )

        return instance
