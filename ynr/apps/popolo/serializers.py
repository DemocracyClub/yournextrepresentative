from rest_framework import serializers

from elections.serializers import EmbeddedPostElectionSerializer
from popolo import models as popolo_models


class MinimalPostSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = popolo_models.Post
        fields = ("id", "url", "label", "slug")

    id = serializers.ReadOnlyField(source="slug")
    label = serializers.ReadOnlyField()
    url = serializers.HyperlinkedIdentityField(
        view_name="post-detail", lookup_field="slug", lookup_url_kwarg="slug"
    )


class PostSerializer(MinimalPostSerializer):
    class Meta:
        model = popolo_models.Post
        fields = ("id", "url", "label", "role", "group", "elections")

    role = serializers.ReadOnlyField()

    elections = EmbeddedPostElectionSerializer(
        many=True, read_only=True, source="ballot_set"
    )
