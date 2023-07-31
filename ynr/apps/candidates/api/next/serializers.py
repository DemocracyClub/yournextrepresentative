from candidates import models as candidates_models
from elections.api.next.serializers import MinimalBallotSerializer
from people.api.next.serializers import MinimalPersonSerializer
from rest_framework import serializers


class LoggedActionSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = candidates_models.LoggedAction
        fields = (
            "id",
            "url",
            "user",
            "person",
            "person_pk",
            "ballot",
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
    ballot = MinimalBallotSerializer(read_only=True)
