from rest_framework import serializers

from candidates import models as candidates_models
from people.api.next.serializers import MinimalPersonSerializer


class LoggedActionSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = candidates_models.LoggedAction
        fields = (
            "id",
            "url",
            "user",
            "person",
            "action_type",
            "person_new_version",
            "created",
            "updated",
            "source",
        )

    person_new_version = serializers.ReadOnlyField(
        source="popit_person_new_version"
    )
    user = serializers.ReadOnlyField(source="user.username")
    person = MinimalPersonSerializer(read_only=True)
