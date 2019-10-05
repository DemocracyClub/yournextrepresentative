from rest_framework import serializers
from sorl_thumbnail_serializer.fields import HyperlinkedSorlImageField

import people.models
from candidates import models as candidates_models
from people.models import PersonImage
from popolo import models as popolo_models


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


class PersonBallotsSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = popolo_models.Membership
        fields = (
            "ballot",
            # "party",
            "elected",
            "party_list_position",
        )

    ballot = serializers.HyperlinkedRelatedField(
        read_only=True,
        view_name="ballot-detail",
        lookup_field="ballot_paper_id",
        lookup_url_kwarg="ballot_paper_id",
    )


class PersonSerializer(MinimalPersonSerializer):
    class Meta:
        model = people.models.Person
        fields = (
            "id",
            "url",
            "honorific_prefix",
            "name",
            "honorific_suffix",
            "other_names",
            "sort_name",
            "identifiers",
            "ballots",
            "email",
            "gender",
            "birth_date",
            "death_date",
            "images",
            "thumbnail",
            "favourite_biscuit",
        )

    identifiers = PersonIdentifierSerializer(
        many=True, read_only=True, source="tmp_person_identifiers"
    )
    other_names = OtherNameSerializer(many=True, read_only=True)
    images = ImageSerializer(many=True, read_only=True, default=[])
    email = serializers.SerializerMethodField()
    ballots = serializers.SerializerMethodField()

    thumbnail = SizeLimitedHyperlinkedSorlImageField(
        "300x300",
        options={"crop": "center"},
        source="primary_image",
        read_only=True,
    )

    def get_email(self, obj):
        return obj.get_email

    def get_ballots(self, obj):
        qs = (
            obj.memberships.all()
            .select_related("ballot", "party")
            .order_by("ballot__election__election_date")
        )
        ballots = []
        for ballot in qs:
            ballots.append(
                PersonBallotsSerializer(
                    ballot, context={"request": self.context["request"]}
                ).data
            )
        return ballots


class PersonRedirectSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = candidates_models.PersonRedirect
        fields = ("id", "url", "old_person_id", "new_person_id")

    url = serializers.HyperlinkedIdentityField(
        view_name="personredirect-detail",
        lookup_field="old_person_id",
        lookup_url_kwarg="old_person_id",
    )
