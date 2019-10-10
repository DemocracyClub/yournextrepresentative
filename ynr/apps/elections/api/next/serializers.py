from rest_framework import serializers

from api.next.serializers import OrganizationSerializer
from candidates import models as candidates_models
from elections import models as election_models
from official_documents.api.next.serializers import OfficialDocumentSerializer
from popolo.api.next.serializers import (
    CandidacyOnBallotSerializer,
    MinimalPostSerializer,
)
from utils.db import LastWord
from uk_results.models import ResultSet


class ResultOnBallotSerializer(serializers.ModelSerializer):
    class Meta:
        model = ResultSet
        fields = ("num_turnout_reported", "num_spoilt_ballots", "source")


class MinimalElectionSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = election_models.Election
        fields = ("election_id", "url", "name", "election_date", "current")

    election_id = serializers.ReadOnlyField(source="slug")

    url = serializers.HyperlinkedIdentityField(
        view_name="election-detail",
        lookup_field="slug",
        lookup_url_kwarg="slug",
    )


class ElectionSerializer(MinimalElectionSerializer):
    class Meta:
        model = election_models.Election
        fields = (
            "slug",
            "url",
            "name",
            "election_date",
            "current",
            "organization",
            "party_lists_in_use",
            "ballots",
        )

    organization = OrganizationSerializer(read_only=True)
    ballots = serializers.HyperlinkedRelatedField(
        source="ballot_set",
        view_name="ballot-detail",
        read_only=True,
        lookup_field="ballot_paper_id",
        many=True,
    )


class BallotSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = candidates_models.Ballot
        fields = (
            "url",
            "history_url",
            "election",
            "post",
            "winner_count",
            "ballot_paper_id",
            "cancelled",
            "sopn",
            "candidates_locked",
            "candidacies",
            "results",
        )

    url = serializers.HyperlinkedIdentityField(
        view_name="ballot-detail",
        lookup_field="ballot_paper_id",
        lookup_url_kwarg="ballot_paper_id",
    )

    history_url = serializers.HyperlinkedIdentityField(
        view_name="ballot-history",
        lookup_field="ballot_paper_id",
        lookup_url_kwarg="ballot_paper_id",
    )

    election = MinimalElectionSerializer(read_only=True)
    post = MinimalPostSerializer(read_only=True)
    sopn = OfficialDocumentSerializer(read_only=True)
    candidacies = serializers.SerializerMethodField()
    results = serializers.SerializerMethodField()

    def get_candidacies(self, instance):
        qs = (
            instance.membership_set.all()
            .select_related("result", "person", "party")
            .annotate(last_name=LastWord("person__name"))
        )

        order_by = ["-elected", "-result__is_winner", "-result__num_ballots"]
        if instance.election.party_lists_in_use:
            order_by += ["party__name", "party_list_position"]
        else:
            order_by += ["person__sort_name", "last_name"]
        qs = qs.order_by(*order_by)
        return CandidacyOnBallotSerializer(
            qs, many=True, context=self.context
        ).data

    def get_results(self, obj):
        resultset = getattr(obj, "resultset", None)
        if resultset:
            return ResultOnBallotSerializer(
                resultset, context=self.context
            ).data
        return None
