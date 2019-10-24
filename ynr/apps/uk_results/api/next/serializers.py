from rest_framework import serializers
from rest_framework.reverse import reverse

from parties.api.next.serializers import MinimalPartySerializer
from popolo.api.next.serializers import (
    MinimalBallotSerializer,
    PersonOnBallotSerializer,
)
from uk_results.models import ResultSet, CandidateResult


class CandidateResultSerializer(serializers.ModelSerializer):
    class Meta:
        model = CandidateResult
        fields = (
            "person",
            "party",
            "party_list_position",
            "num_ballots",
            "elected",
        )
        ref_name = None  # Tells swagger that this is always embedded

    elected = serializers.ReadOnlyField(source="is_winner")
    person = serializers.SerializerMethodField()
    party_list_position = serializers.ReadOnlyField(
        source="membership__party_list_position"
    )
    party = serializers.SerializerMethodField()

    def get_person(self, obj):
        return PersonOnBallotSerializer(
            obj.membership.person, context=self.context
        ).data

    def get_party(self, obj):
        return MinimalPartySerializer(
            obj.membership.party, context=self.context
        ).data


class ResultSerializer(serializers.ModelSerializer):
    class Meta:
        model = ResultSet
        fields = (
            "url",
            "num_turnout_reported",
            "num_spoilt_ballots",
            "source",
            "ballot",
            "candidate_results",
        )

    url = serializers.SerializerMethodField()

    def get_url(self, obj):
        return reverse(
            "resultset-detail",
            kwargs={"ballot_paper_id": obj.ballot.ballot_paper_id},
            request=self.context["request"],
        )

    ballot = MinimalBallotSerializer()
    candidate_results = CandidateResultSerializer(many=True)
