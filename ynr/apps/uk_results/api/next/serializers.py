from parties.api.next.serializers import MinimalPartySerializer
from popolo.api.next.serializers import (
    CANDIDACY_ON_PERSON_FIELDS,
    BallotOnCandidacySerializer,
    CandidacyOnBallotSerializer,
    PersonOnBallotSerializer,
)
from popolo.models import Membership
from rest_framework import serializers
from rest_framework.reverse import reverse
from uk_results.models import CandidateResult, ResultSet


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

    elected = serializers.ReadOnlyField(source="membership.elected")
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
            "turnout_percentage",
            "num_spoilt_ballots",
            "source",
            "ballot",
            "candidate_results",
            "total_electorate",
        )

    url = serializers.SerializerMethodField()

    def get_url(self, obj):
        return reverse(
            "resultset-detail",
            kwargs={"ballot_paper_id": obj.ballot.ballot_paper_id},
            request=self.context["request"],
        )

    ballot = BallotOnCandidacySerializer()
    candidate_results = CandidateResultSerializer(many=True)


class MinimalResultSerializer(serializers.ModelSerializer):
    class Meta:
        model = ResultSet
        fields = (
            "num_turnout_reported",
            "turnout_percentage",
            "num_spoilt_ballots",
            "source",
            "total_electorate",
        )
        extra_kwargs = {"turnout_percentage": {"coerce_to_string": False}}

        ref_name = None  # Tells swagger that this is always embedded


class ElectedSerializer(CandidacyOnBallotSerializer):
    class Meta:
        model = Membership
        fields = CANDIDACY_ON_PERSON_FIELDS + ["ballot", "person"]

    def get_person(self, obj):
        return PersonOnBallotSerializer(obj.person, context=self.context).data
