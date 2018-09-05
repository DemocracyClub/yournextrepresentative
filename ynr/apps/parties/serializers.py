from rest_framework import serializers

from parties.models import Party, PartyDescription, PartyEmblem


class PartySerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Party
        fields = (
            "ec_id",
            "url",
            "name",
            "register",
            "status",
            "date_registered",
            "date_deregistered",
            "default_emblem",
        )
        extra_kwargs = {"url": {"lookup_field": "ec_id"}}
