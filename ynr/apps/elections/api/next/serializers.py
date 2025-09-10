from api.next.serializers import OrganizationSerializer
from candidates import models as candidates_models
from drf_yasg import openapi
from drf_yasg.utils import swagger_serializer_method
from elections import models as election_models
from official_documents.api.next.serializers import BallotSOPNSerializer
from official_documents.models import BallotSOPN
from popolo.api.next.serializers import (
    CandidacyOnBallotSerializer,
    MinimalPostSerializer,
)
from rest_framework import serializers
from uk_results.api.next.serializers import MinimalResultSerializer


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


class TagsField(serializers.JSONField):
    class Meta:
        swagger_schema_fields = {
            "type": openapi.TYPE_OBJECT,
            "title": "Tags",
            "description": """Freeform tags, but typically contain NUTS1 tags
                    for the ballot. Don't rely on this data existing, defaults to an 
                    empty object""",
            "properties": {
                "NUTS1": {
                    "type": openapi.TYPE_OBJECT,
                    "properties": {
                        "key": {
                            "type": openapi.TYPE_STRING,
                            "example": "UKM",
                            "description": "The key representing the NUTS1 code (e.g., UKM for Scotland).",
                        },
                        "value": {
                            "type": openapi.TYPE_STRING,
                            "example": "Scotland",
                            "description": "The human-readable name associated with the NUTS1 code.",
                        },
                    },
                    "description": "An object containing NUTS1 tag details.",
                    "example": {"key": "UKM", "value": "Scotland"},
                }
            },
            "example": {
                "NUTS1": {"key": "UKM", "value": "Scotland"},
            },
        }


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
            "replaces",
            "replaced_by",
            "uncontested",
            "results",
            "voting_system",
            "tags",
            "by_election_reason",
        )

    replaces = serializers.SlugRelatedField(
        read_only=True, slug_field="ballot_paper_id"
    )
    replaced_by = serializers.SlugRelatedField(
        read_only=True, slug_field="ballot_paper_id"
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
    results = MinimalResultSerializer(read_only=True, source="resultset")

    results_url = serializers.HyperlinkedIdentityField(
        view_name="resultset-detail",
        lookup_field="ballot_paper_id",
        lookup_url_kwarg="ballot_paper_id",
    )
    last_updated = serializers.SerializerMethodField()
    cancelled = serializers.SerializerMethodField()
    tags = TagsField()

    def get_last_updated(self, instance):
        """
        If the last_updated value has been annoated, return that, otherwise use
        the modified date on the ballot instance
        """
        return getattr(instance, "last_updated", instance.modified)

    @swagger_serializer_method(serializer_or_field=BallotSOPNSerializer)
    def get_sopn(self, instance):
        try:
            return BallotSOPNSerializer(
                instance=instance.sopn, read_only=True
            ).data
        except BallotSOPN.DoesNotExist:
            return None

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
                "-result__num_ballots",
                "party__name",
                "party_list_position",
            ]
            qs = qs.order_by(*order_by)
        return CandidacyOnBallotSerializer(
            qs, many=True, context=self.context
        ).data

    def get_cancelled(self, instance):
        """
        If the ballot is marked as cancelled, return True. Otherwise check if
        it was uncontested, as we may know this before it has been marked as
        cancelled in EE.
        """
        if instance.cancelled:
            return True
        return instance.uncontested
