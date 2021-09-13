from drf_yasg.utils import swagger_serializer_method
from rest_framework import serializers
from sorl_thumbnail_serializer.fields import HyperlinkedSorlImageField

import people.models
from candidates import models as candidates_models
from people.models import PersonImage
from popolo import models as popolo_models
from popolo.api.next.serializers import CandidacyOnPersonSerializer


class SizeLimitedHyperlinkedSorlImageField(HyperlinkedSorlImageField):
    def to_representation(self, value):
        try:
            return super().to_representation(value)
        except ValueError:
            # Chances are the image is too large
            return None


class ImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = PersonImage
        fields = (
            "id",
            "source",
            "is_primary",
            "md5sum",
            "copyright",
            "uploading_user",
            "user_notes",
            "user_copyright",
            "notes",
            "image_url",
        )

    image_url = serializers.SerializerMethodField()
    uploading_user = serializers.ReadOnlyField(source="uploading_user.username")

    @swagger_serializer_method(serializer_or_field=serializers.URLField)
    def get_image_url(self, instance):
        return instance.image.url


class OtherNameSerializer(serializers.ModelSerializer):
    class Meta:
        model = popolo_models.OtherName
        fields = ("name", "note")
        ref_name = None  # Tells swagger that this is always embedded


class ContactDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = popolo_models.ContactDetail
        fields = ("contact_type", "label", "note", "value")

        last_updated = serializers.DateTimeField(source="modified")


class SourceSerializer(serializers.ModelSerializer):
    class Meta:
        model = popolo_models.Source
        fields = ("note", "url")


class PersonIdentifierSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = people.models.PersonIdentifier
        ref_name = None  # Tells swagger that this is always embedded
        fields = ("value", "value_type", "internal_identifier")


class MinimalPersonSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = people.models.Person
        ref_name = None  # Tells swagger that this is always embedded
        fields = ("id", "url", "name")


class PersonSerializer(MinimalPersonSerializer):
    class Meta:
        model = people.models.Person
        fields = (
            "id",
            "url",
            "versions_url",
            "history_url",
            "created",
            "last_updated",
            "honorific_prefix",
            "name",
            "honorific_suffix",
            "other_names",
            "sort_name",
            "identifiers",
            "candidacies",
            "email",
            "gender",
            "birth_date",
            "death_date",
            "images",
            "thumbnail",
            "statement_to_voters",
            "favourite_biscuit",
        )

    versions_url = serializers.HyperlinkedIdentityField(
        view_name="person-versions"
    )
    history_url = serializers.HyperlinkedIdentityField(
        view_name="person-history"
    )
    last_updated = serializers.DateTimeField(source="modified")
    identifiers = PersonIdentifierSerializer(
        many=True, read_only=True, source="tmp_person_identifiers"
    )
    other_names = OtherNameSerializer(many=True, read_only=True)
    images = ImageSerializer(many=True, read_only=True, default=[])
    email = serializers.SerializerMethodField()
    candidacies = serializers.SerializerMethodField()
    statement_to_voters = serializers.CharField(
        source="biography", allow_blank=True
    )
    favourite_biscuit = serializers.CharField(allow_null=True, allow_blank=True)
    thumbnail = serializers.SerializerMethodField()

    def get_thumbnail(self, instance):
        try:
            image = instance.images.all()[0]
        except IndexError:
            return None

        return SizeLimitedHyperlinkedSorlImageField(
            "300x300", options={"crop": "center"}, read_only=True, use_url=True
        ).to_representation(image.image)

    def get_email(self, obj):
        return obj.get_email

    @swagger_serializer_method(serializer_or_field=CandidacyOnPersonSerializer)
    def get_candidacies(self, obj):
        qs = obj.memberships.all()
        return CandidacyOnPersonSerializer(
            qs, many=True, context={"request": self.context["request"]}
        ).data


class PersonRedirectSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = candidates_models.PersonRedirect
        fields = (
            "id",
            "url",
            "old_person_id",
            "new_person_id",
            "new_person_url",
        )

    url = serializers.HyperlinkedIdentityField(
        view_name="personredirect-detail",
        lookup_field="old_person_id",
        lookup_url_kwarg="old_person_id",
    )

    new_person_url = serializers.HyperlinkedIdentityField(
        view_name="person-detail",
        lookup_field="new_person_id",
        lookup_url_kwarg="pk",
    )
