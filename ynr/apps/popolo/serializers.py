from rest_framework import serializers

from popolo import models as popolo_models
from parties.serializers import MinimalPartySerializer


class MinimalPostSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = popolo_models.Post
        fields = ("id", "url", "label", "slug")

    id = serializers.ReadOnlyField(source="slug")
    label = serializers.ReadOnlyField()
    url = serializers.HyperlinkedIdentityField(
        view_name="post-detail", lookup_field="slug", lookup_url_kwarg="slug"
    )


class NominationAndResultSerializer(serializers.HyperlinkedModelSerializer):
    """
    A representation of a Membership with only the information on the ballot
    paper, and results if we have them.

    """

    class Meta:
        model = popolo_models.Membership
        fields = ("elected", "party_list_position", "person", "party")

    elected = serializers.ReadOnlyField()
    party_list_position = serializers.ReadOnlyField()
    person = serializers.ReadOnlyField(source="person.name")
    party = MinimalPartySerializer(read_only=True)
