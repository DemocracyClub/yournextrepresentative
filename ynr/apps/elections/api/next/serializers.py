from drf_yasg.utils import swagger_serializer_method

from rest_framework import serializers

from api.next.serializers import OrganizationSerializer
from candidates import models as candidates_models
from elections import models as election_models
from official_documents.api.next.serializers import OfficialDocumentSerializer
from popolo.api.next.serializers import (
    CandidacyOnBallotSerializer,
    MinimalPostSerializer,
)


class MinimalElectionSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = election_models.Election
        ref_name = None  # Tells swagger that this is always embedded

        fields = (
            "election_id",
            "url",
            "name",
            "election_date",
            "current",
            "party_lists_in_use",
            "created",
            "last_updated",
        )

    election_id = serializers.ReadOnlyField(
        source="slug", label="An election ID"
    )

    url = serializers.HyperlinkedIdentityField(
        view_name="election-detail",
        lookup_field="slug",
        lookup_url_kwarg="slug",
    )

    last_updated = serializers.DateTimeField(source="modified")


class MinimalBallotSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = candidates_models.Ballot
        ref_name = None  # Tells swagger that this is always embedded
        fields = ("url", "ballot_paper_id")

    url = serializers.HyperlinkedIdentityField(
        view_name="ballot-detail",
        lookup_field="ballot_paper_id",
        lookup_url_kwarg="ballot_paper_id",
    )


class ElectionTypeSerializer(serializers.Serializer):
    slug = serializers.CharField(max_length=50)
    label = serializers.CharField(max_length=100, source="for_post_role")


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
    ballots = serializers.SerializerMethodField(read_only=True)

    @swagger_serializer_method(serializer_or_field=MinimalBallotSerializer)
    def get_ballots(self, obj):
        return MinimalBallotSerializer(
            obj.ballot_set, many=True, context=self.context
        ).data


class BallotSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = candidates_models.Ballot
        fields = (
            "url",
            "history_url",
            "results_url",
            "election",
            "post",
            "winner_count",
            "ballot_paper_id",
            "cancelled",
            "sopn",
            "candidates_locked",
            "candidacies",
            "created",
            "last_updated",
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
    sopn = serializers.SerializerMethodField()
    candidacies = serializers.SerializerMethodField()

    results_url = serializers.HyperlinkedIdentityField(
        view_name="resultset-detail",
        lookup_field="ballot_paper_id",
        lookup_url_kwarg="ballot_paper_id",
    )
    last_updated = serializers.DateTimeField(source="modified")

    @swagger_serializer_method(serializer_or_field=OfficialDocumentSerializer)
    def get_sopn(self, instance):
        try:
            sopn = instance.officialdocument_set.all()[0]
        except IndexError:
            return None

        return OfficialDocumentSerializer(instance=sopn, read_only=True).data

    @swagger_serializer_method(serializer_or_field=CandidacyOnBallotSerializer)
    def get_candidacies(self, instance):
        """
        A candidacy represents a `Person` standing on this `Ballot`.

        This is different to simply insluding a `Person` object, as a person
        can stand more than once, and stand for different parties.
        """
        qs = instance.membership_set.all()

        if instance.election.party_lists_in_use:
            order_by = [
                "-elected",
                "-result__is_winner",
                "-result__num_ballots",
                "party__name",
                "party_list_position",
            ]
            qs = qs.order_by(*order_by)
        return CandidacyOnBallotSerializer(
            qs, many=True, context=self.context
        ).data
