from drf_yasg.utils import swagger_serializer_method
from rest_framework import serializers

from facebook_data.models import FacebookAdvert
from popolo.api.next.serializers import PersonOnBallotSerializer


class FacebookAdvertSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = FacebookAdvert
        fields = ("ad_id", "ad_json", "person", "associated_url", "image")
        swagger_schema_fields = {"description": model.__doc__}

    ad_json = serializers.SerializerMethodField(
        help_text="The JSON object returned from the Facebook "
        "Graph API for this advert"
    )
    person = serializers.SerializerMethodField()

    @swagger_serializer_method(serializer_or_field=PersonOnBallotSerializer)
    def get_person(self, obj):
        return PersonOnBallotSerializer(obj.person, context=self.context).data

    def get_ad_json(self, obj):
        data = obj.ad_json
        try:
            del data["ad_snapshot_url"]
        except KeyError:
            pass
        return data
