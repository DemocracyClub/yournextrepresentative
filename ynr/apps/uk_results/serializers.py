from rest_framework import serializers

from candidates.serializers import MembershipSerializer

from .models import CandidateResult, ResultSet


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
    # result_set = ResultSetSerializer(read_only=True)


class ResultSetSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = ResultSet
        fields = (
            "id",
            "url",
            "candidate_results",
            "num_turnout_reported",
            "num_spoilt_ballots",
            "user",
            "user_id",
            "ballot_paper_id",
        )

    # post_result = PostResultSerializer()
    user = serializers.ReadOnlyField(source="user.username")
    ballot_paper_id = serializers.ReadOnlyField(
        source="post_election.ballot_paper_id"
    )
    user_id = serializers.ReadOnlyField(source="user.id")
    candidate_results = CandidateResultSerializer(many=True, read_only=True)
