from rest_framework import serializers

from popolo import models as popolo_models
from candidates import models as candidates_models
from parties.api.next.serializers import MinimalPartySerializer
from people.models import Person
from uk_results.models import CandidateResult


class PersonOnBallotSerializer(serializers.HyperlinkedModelSerializer):
    """
    Just used for showing people o ballots
    """

    class Meta:
        model = Person
        fields = ("id", "url", "name")


class MinimalPostSerializer(serializers.ModelSerializer):
    class Meta:
        model = popolo_models.Post
        ref_name = None  # Tells swagger that this is always embedded
        fields = ("id", "label", "slug")

    id = serializers.ReadOnlyField(source="slug")
    label = serializers.ReadOnlyField()


class MinimalBallotSerializer(serializers.HyperlinkedModelSerializer):
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

    elected = serializers.ReadOnlyField(source="is_winner")


BASE_CANDIDACY_FIELDS = ["elected", "party_list_position", "party"]

CANDIDACY_ON_BALLOT_FIELDS = BASE_CANDIDACY_FIELDS + ["person", "result"]
CANDIDACY_ON_PERSON_FIELDS = BASE_CANDIDACY_FIELDS + ["ballot"]


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

    def get_ballot(self, obj):
        return MinimalBallotSerializer(
            obj.ballot, read_only=True, context=self.context
        ).data

    def get_person(self, obj):
        return PersonOnBallotSerializer(obj.person, context=self.context).data

    def get_result(self, obj):
        result = getattr(obj, "result", None)
        if result:
            return CandidacyResultsSerializer(
                result, read_only=True, context=self.context
            ).data
        return None

    def get_party(self, obj):
        return MinimalPartySerializer(obj.party, context=self.context).data


class CandidacyOnBallotSerializer(CandidacySerializer):
    """
    A subclass of CandidacySerializer that will be used on the Ballot endpoint

    """

    class Meta:
        model = popolo_models.Membership
        fields = CANDIDACY_ON_BALLOT_FIELDS


class CandidacyOnPersonSerializer(CandidacySerializer):
    """
    A subclass of CandidacySerializer that will be used on the Person endpoint

    """

    class Meta:
        model = popolo_models.Membership
        fields = CANDIDACY_ON_PERSON_FIELDS
