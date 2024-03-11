# v0.9 is legacy code
import people.models
from candidates import models as candidates_models
from elections import models as election_models
from parties.models import Party
from people.models import PersonImage
from popolo import models as popolo_models
from rest_framework import serializers
from rest_framework.fields import JSONField
from sorl_thumbnail_serializer.fields import HyperlinkedSorlImageField

# These are serializer classes from the Django-REST-framework API
#
# For most objects there are two serializers - a full one and a
# minimal one.  The minimal ones (whose class names begin 'Minimal')
# are used for serializing the objects when they're just being
# included as related objects, rather than the resource that
# information is being requested about.
#
# e.g. if you request information about a Post via the 'posts'
# endpoint, it's pretty useful to have the ID, URL and name of the
# elections that the Post is part of, but you probably don't need
# every bit of election metadata.  A request to the 'elections'
# endpoint, however, would include full metadata about the elections.
#
# This reduces the bloat of API responses, at the cost of some users
# having to make extra queries.


class OtherNameSerializer(serializers.ModelSerializer):
    class Meta:
        model = popolo_models.OtherName
        fields = ("name", "note")


class IdentifierSerializer(serializers.ModelSerializer):
    class Meta:
        model = popolo_models.Identifier
        fields = ("identifier", "scheme")


class ContactDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = popolo_models.ContactDetail
        fields = ("contact_type", "label", "note", "value")


class SourceSerializer(serializers.ModelSerializer):
    class Meta:
        model = popolo_models.Source
        fields = ("note", "url")


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
    is_primary = serializers.SerializerMethodField()

    def get_image_url(self, i):
        return i.image.url

    def get_is_primary(self, obj):
        """
        This is hardcoded to maintain backwards compatibility for v0.9 after
        changing the PersonImage model to use a OneToOne with Person
        """
        return True


class FakeMinimalOrganizationSerializer(serializers.HyperlinkedModelSerializer):
    """
    Because we don't have the relationship between Organisation and Membership
    any more, we have to fake the 'on_behalf_of' realtionship in the API
    """

    class Meta:
        model = Party
        fields = ("id", "name")

    id = serializers.ReadOnlyField(source="legacy_slug")


class MinimalOrganizationSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = popolo_models.Organization
        fields = ("id", "url", "name")

    id = serializers.ReadOnlyField(source="slug")
    url = serializers.HyperlinkedIdentityField(
        view_name="organization-detail",
        lookup_field="slug",
        lookup_url_kwarg="slug",
    )


class PartySetSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = candidates_models.PartySet
        fields = ("id", "url", "name", "slug")


class OrganizationSerializer(MinimalOrganizationSerializer):
    class Meta:
        model = popolo_models.Organization
        fields = (
            "id",
            "url",
            "name",
            "other_names",
            "identifiers",
            "classification",
            "parent",
            "founding_date",
            "dissolution_date",
            "contact_details",
            "images",
            "links",
            "sources",
            "register",
            "party_sets",
        )

    parent = MinimalOrganizationSerializer(allow_null=True)

    contact_details = ContactDetailSerializer(many=True, read_only=True)
    identifiers = IdentifierSerializer(many=True, read_only=True)
    links = serializers.SerializerMethodField()
    other_names = OtherNameSerializer(many=True, read_only=True)
    sources = SourceSerializer(many=True, read_only=True)
    images = ImageSerializer(many=True, read_only=True)

    party_sets = PartySetSerializer(many=True, read_only=True)

    def get_links(self, obj):
        return []


class MinimalElectionSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = election_models.Election
        fields = ("id", "url", "name")

    id = serializers.ReadOnlyField(source="slug")
    url = serializers.HyperlinkedIdentityField(
        view_name="election-detail",
        lookup_field="slug",
        lookup_url_kwarg="slug",
    )


class ElectionSerializer(MinimalElectionSerializer):
    class Meta:
        model = election_models.Election
        fields = (
            "id",
            "url",
            "name",
            "for_post_role",
            "winner_membership_role",
            "candidate_membership_role",
            "election_date",
            "current",
            "use_for_candidate_suggestions",
            "organization",
            "party_lists_in_use",
            "default_party_list_members_to_show",
            "show_official_documents",
            "ocd_division",
            "description",
        )

    organization = MinimalOrganizationSerializer(read_only=True)


class MinimalPostSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = popolo_models.Post
        fields = ("id", "url", "label", "slug")

    id = serializers.ReadOnlyField(source="identifier")
    label = serializers.ReadOnlyField()
    url = serializers.HyperlinkedIdentityField(
        view_name="post-detail", lookup_field="slug", lookup_url_kwarg="slug"
    )


class MinimalPersonSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = people.models.Person
        fields = ("id", "url", "name")


class MembershipSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = popolo_models.Membership
        fields = (
            "id",
            "url",
            "label",
            "role",
            "elected",
            "party_list_position",
            "person",
            "on_behalf_of",
            "post",
            "start_date",
            "end_date",
            "election",
        )

    elected = serializers.ReadOnlyField()
    party_list_position = serializers.ReadOnlyField()
    person = MinimalPersonSerializer(read_only=True)
    on_behalf_of = FakeMinimalOrganizationSerializer(
        read_only=True, source="party"
    )
    post = MinimalPostSerializer(read_only=True)

    election = MinimalElectionSerializer(source="ballot.election")


class PostElectionSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = candidates_models.Ballot
        fields = (
            "id",
            "url",
            "post",
            "election",
            "winner_count",
            "ballot_paper_id",
            "cancelled",
        )

    post = MinimalPostSerializer(read_only=True)
    election = MinimalElectionSerializer(read_only=True)


class PersonSerializer(MinimalPersonSerializer):
    class Meta:
        model = people.models.Person
        fields = (
            "id",
            "url",
            "name",
            "other_names",
            "identifiers",
            "honorific_prefix",
            "honorific_suffix",
            "sort_name",
            "email",
            "gender",
            "birth_date",
            "death_date",
            "versions",
            "contact_details",
            "links",
            "memberships",
            "images",
            "extra_fields",
            "thumbnail",
        )

    links = serializers.SerializerMethodField()
    other_names = OtherNameSerializer(many=True, read_only=True)
    images = serializers.SerializerMethodField()

    email = serializers.SerializerMethodField()

    versions = JSONField(read_only=True)

    memberships = MembershipSerializer(many=True, read_only=True)

    extra_fields = serializers.SerializerMethodField()
    contact_details = serializers.SerializerMethodField()
    identifiers = serializers.SerializerMethodField()

    thumbnail = HyperlinkedSorlImageField(
        "300x300",
        options={"crop": "center"},
        source="person_image",
        read_only=True,
    )

    def get_extra_fields(self, obj):
        return [{"favourite_biscuits": obj.favourite_biscuit or ""}]

    def get_contact_details(self, obj):
        ret = []
        if obj.get_twitter_username:
            ret.append(
                {
                    "contact_type": "twitter",
                    "label": "",
                    "note": "",
                    "value": obj.get_twitter_username,
                }
            )
        return ret

    def get_identifiers(self, obj):
        ret = []
        if obj.get_single_identifier_value("theyworkforyou"):
            ret.append(
                {
                    "identifier": obj.get_single_identifier_value(
                        "theyworkforyou"
                    ),
                    "scheme": "uk.org.publicwhip",
                }
            )
        if obj.get_single_identifier_value("twitter_username"):
            ret.append(
                {
                    "identifier": obj.get_single_identifier_of_type(
                        "twitter_username"
                    ).internal_identifier,
                    "scheme": "twitter",
                }
            )
        return ret

    def get_email(self, obj):
        return obj.get_email

    def get_links(self, obj):
        """
        :type obj: people.models.Person
        """
        links = []
        notes_tp_pi_types = {
            "homepage": "homepage_url",
            "facebook personal": "facebook_personal_url",
            "party candidate page": "party_ppc_page_url",
            "linkedin": "linkedin_url",
            "facebook page": "facebook_page_url",
            "wikipedia": "wikipedia_url",
            "blue_sky_url": "blue_sky_url",
            "threads_url": "threads_url",
            "tiktok_url": "tiktok_url",
            "other_url": "other_url",
        }
        pi_types_to_notes = {v: k for k, v in notes_tp_pi_types.items()}
        qs = obj.tmp_person_identifiers.filter(
            value_type__in=pi_types_to_notes.values()
        )
        for pi in qs:
            links.append(
                {"note": pi_types_to_notes[pi.value_type], "url": pi.value}
            )
        return links

    def get_images(self, obj):
        """
        To maintain backwards compatibility return image as a list even though
        a person can only have a single image
        """
        try:
            return [ImageSerializer(instance=obj.image, read_only=True).data]
        except PersonImage.DoesNotExist:
            return []


class NoVersionPersonSerializer(PersonSerializer):
    class Meta:
        model = people.models.Person
        fields = (
            "id",
            "url",
            "name",
            "other_names",
            "identifiers",
            "honorific_prefix",
            "honorific_suffix",
            "sort_name",
            "email",
            "gender",
            "birth_date",
            "death_date",
            "contact_details",
            "links",
            "memberships",
            "images",
            "extra_fields",
            "thumbnail",
        )


class EmbeddedPostElectionSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = candidates_models.Ballot
        fields = (
            "winner_count",
            "candidates_locked",
            "name",
            "id",
            "url",
            "ballot_paper_id",
            "cancelled",
        )

    name = serializers.ReadOnlyField(source="election.name")
    id = serializers.ReadOnlyField(source="election.slug")
    winner_count = serializers.ReadOnlyField()


class PostSerializer(MinimalPostSerializer):
    class Meta:
        model = popolo_models.Post
        fields = (
            "id",
            "url",
            "label",
            "role",
            "group",
            "party_set",
            "organization",
            "elections",
            "memberships",
        )

    role = serializers.ReadOnlyField()
    party_set = PartySetSerializer(read_only=True)

    memberships = MembershipSerializer(many=True, read_only=True)

    organization = MinimalOrganizationSerializer()

    elections = EmbeddedPostElectionSerializer(
        many=True, read_only=True, source="ballot_set"
    )


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


class PersonRedirectSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = candidates_models.PersonRedirect
        fields = ("id", "url", "old_person_id", "new_person_id")

    url = serializers.HyperlinkedIdentityField(
        view_name="personredirect-detail",
        lookup_field="old_person_id",
        lookup_url_kwarg="old_person_id",
    )
