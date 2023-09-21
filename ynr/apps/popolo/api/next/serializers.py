from candidates import models as candidates_models
from drf_yasg.utils import swagger_serializer_method
from parties.api.next.serializers import MinimalPartySerializer
from people.models import Person
from popolo import models as popolo_models
from rest_framework import serializers
from uk_results.models import CandidateResult


class PersonOnBallotSerializer(serializers.HyperlinkedModelSerializer):
    """
    Just used for showing people o ballots
    """

    class Meta:
        model = Person
        fields = ("id", "url", "name")
        ref_name = None  # Tells swagger that this is always embedded


class MinimalPostSerializer(serializers.ModelSerializer):
    class Meta:
        model = popolo_models.Post
        ref_name = None  # Tells swagger that this is always embedded
        fields = ("id", "label", "slug", "created", "last_updated")

    id = serializers.ReadOnlyField(source="identifier")
    slug = serializers.ReadOnlyField()
    label = serializers.ReadOnlyField()
    last_updated = serializers.DateTimeField(source="modified")


class BallotOnCandidacySerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = candidates_models.Ballot
        fields = ("url", "ballot_paper_id")
        ref_name = None  # Tells swagger that this is always embedded

    url = serializers.HyperlinkedIdentityField(
        view_name="ballot-detail",
        lookup_field="ballot_paper_id",
        lookup_url_kwarg="ballot_paper_id",
    )


class CandidacyResultsSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = CandidateResult
        fields = ("elected", "num_ballots")
        ref_name = None  # Tells swagger that this is always embedded

    elected = serializers.ReadOnlyField(source="membership.elected")


BASE_CANDIDACY_FIELDS = [
    "elected",
    "party_list_position",
    "party",
    "party_name",
    "party_description_text",
    "deselected",
    "created",
    "modified",
]

CANDIDACY_ON_BALLOT_FIELDS = BASE_CANDIDACY_FIELDS + ["person", "result"]
CANDIDACY_ON_PERSON_FIELDS = BASE_CANDIDACY_FIELDS + [
    "ballot",
    "previous_party_affiliations",
]


class CandidacySerializer(serializers.HyperlinkedModelSerializer):
    """
    Represents what is internally a `Membership`, but what we expose as a
    candidacy publicly.

    Used both on the `Ballot` endpoint and the `Person` endpoint, but in
    slightly different forms
    """

    class Meta:
        model = popolo_models.Membership
        fields = BASE_CANDIDACY_FIELDS
        # exclude = ("ballot", )

    elected = serializers.ReadOnlyField()
    party_list_position = serializers.ReadOnlyField()
    party = serializers.SerializerMethodField()
    person = serializers.SerializerMethodField(read_only=True)
    ballot = serializers.SerializerMethodField()
    result = serializers.SerializerMethodField()
    previous_party_affiliations = MinimalPartySerializer(
        read_only=True, many=True
    )
    deselected = serializers.ReadOnlyField()

    @swagger_serializer_method(serializer_or_field=BallotOnCandidacySerializer)
    def get_ballot(self, obj):
        return BallotOnCandidacySerializer(
            obj.ballot, read_only=True, context=self.context
        ).data

    @swagger_serializer_method(serializer_or_field=PersonOnBallotSerializer)
    def get_person(self, obj):
        return PersonOnBallotSerializer(obj.person, context=self.context).data

    @swagger_serializer_method(serializer_or_field=CandidacyResultsSerializer)
    def get_result(self, obj):
        result = getattr(obj, "result", None)
        if result:
            return CandidacyResultsSerializer(
                result, read_only=True, context=self.context
            ).data
        return None

    @swagger_serializer_method(serializer_or_field=MinimalPartySerializer)
    def get_party(self, obj):
        return MinimalPartySerializer(obj.party, context=self.context).data


class CandidacyOnBallotSerializer(CandidacySerializer):
    """
    A subclass of CandidacySerializer that will be used on the Ballot endpoint

    """

    class Meta:
        model = popolo_models.Membership
        fields = CANDIDACY_ON_BALLOT_FIELDS
        ref_name = None  # Tells swagger that this is always embedded


class CandidacyOnPersonSerializer(CandidacySerializer):
    """
    A subclass of CandidacySerializer that will be used on the Person endpoint

    """

    class Meta:
        model = popolo_models.Membership
        fields = CANDIDACY_ON_PERSON_FIELDS
        ref_name = None  # Tells swagger that this is always embedded
