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

    def get_image_url(self, instance):
        return instance.image.url


class OtherNameSerializer(serializers.ModelSerializer):
    class Meta:
        model = popolo_models.OtherName
        fields = ("name", "note")


class ContactDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = popolo_models.ContactDetail
        fields = ("contact_type", "label", "note", "value")


class SourceSerializer(serializers.ModelSerializer):
    class Meta:
        model = popolo_models.Source
        fields = ("note", "url")


class PersonIdentifierSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = people.models.PersonIdentifier
        fields = ("value", "value_type", "internal_identifier")


class MinimalPersonSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = people.models.Person
        fields = ("id", "url", "name")


class PersonSerializer(MinimalPersonSerializer):
    class Meta:
        model = people.models.Person
        fields = (
            "id",
            "url",
            "versions_url",
            "history_url",
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
            "favourite_biscuit",
        )

    versions_url = serializers.HyperlinkedIdentityField(
        view_name="person-versions"
    )
    history_url = serializers.HyperlinkedIdentityField(
        view_name="person-history"
    )

    identifiers = PersonIdentifierSerializer(
        many=True, read_only=True, source="tmp_person_identifiers"
    )
    other_names = OtherNameSerializer(many=True, read_only=True)
    images = ImageSerializer(many=True, read_only=True, default=[])
    email = serializers.SerializerMethodField()
    candidacies = serializers.SerializerMethodField()

    thumbnail = SizeLimitedHyperlinkedSorlImageField(
        "300x300",
        options={"crop": "center"},
        source="primary_image",
        read_only=True,
    )

    def get_email(self, obj):
        return obj.get_email

    def get_candidacies(self, obj):
        qs = (
            obj.memberships.all()
            .select_related("ballot", "party")
            .order_by("ballot__election__election_date")
        )
        candidacies = []
        for ballot in qs:
            candidacies.append(
                CandidacyOnPersonSerializer(
                    ballot, context={"request": self.context["request"]}
                ).data
            )
        return candidacies


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
