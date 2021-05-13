from rest_framework import serializers

from api.v09.serializers import MembershipSerializer

from uk_results.models import CandidateResult, ResultSet


class CandidateResultSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = CandidateResult
        fields = (
            "id",
            "url",
            "membership",
            "result_set",
            "num_ballots",
            "is_winner",
        )

    membership = MembershipSerializer(read_only=True)
    is_winner = serializers.ReadOnlyField(source="membership.elected")


class ResultSetSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = ResultSet
        fields = (
            "id",
            "url",
            "candidate_results",
            "num_turnout_reported",
            "turnout_percentage",
            "num_spoilt_ballots",
            "user",
            "user_id",
            "ballot_paper_id",
            "total_electorate",
        )

    # post_result = PostResultSerializer()
    user = serializers.ReadOnlyField(source="user.username")
    ballot_paper_id = serializers.ReadOnlyField(source="ballot.ballot_paper_id")
    user_id = serializers.ReadOnlyField(source="user.id")
    candidate_results = CandidateResultSerializer(many=True, read_only=True)
