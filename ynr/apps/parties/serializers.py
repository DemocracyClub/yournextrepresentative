from rest_framework import serializers

from parties.models import Party, PartyDescription, PartyEmblem


class PartyEmblemSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = PartyEmblem
        fields = (
            "image",
            "description",
            "date_approved",
            "ec_emblem_id",
            "default",
        )


class PartyDescriptionSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = PartyDescription
        fields = ("description", "date_description_approved")


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
            "emblems",
            "descriptions",
        )
        extra_kwargs = {"url": {"lookup_field": "ec_id"}}

    default_emblem = PartyEmblemSerializer()
    emblems = PartyEmblemSerializer(many=True)
    descriptions = PartyDescriptionSerializer(many=True)


class MinimalPartySerializer(PartySerializer):
    class Meta:
        model = Party
        fields = ("ec_id", "name")
