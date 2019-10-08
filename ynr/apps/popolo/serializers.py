from rest_framework import serializers

from popolo import models as popolo_models
from parties.serializers import MinimalPartySerializer


class MinimalPostSerializer(serializers.ModelSerializer):
    class Meta:
        model = popolo_models.Post
        fields = ("id", "label", "slug")

    id = serializers.ReadOnlyField(source="slug")
    label = serializers.ReadOnlyField()


class NominationAndResultSerializer(serializers.HyperlinkedModelSerializer):
    """
    A representation of a Membership with only the information on the ballot
    paper, and results if we have them.

    """

    class Meta:
        model = popolo_models.Membership
        fields = ("id", "elected", "party_list_position", "name", "party")

    elected = serializers.ReadOnlyField()
    party_list_position = serializers.ReadOnlyField()
    name = serializers.ReadOnlyField(source="person.name")
    party = MinimalPartySerializer(read_only=True)
