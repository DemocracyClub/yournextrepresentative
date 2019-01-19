from rest_framework import serializers
from sorl_thumbnail_serializer.fields import HyperlinkedSorlImageField

import people.models
from api.helpers import JSONSerializerField
from candidates import models as candidates_models
from elections import models as election_models
from people.serializers import ImageSerializer
from popolo import models as popolo_models
from parties.serializers import MinimalPartySerializer

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


class LinkSerializer(serializers.ModelSerializer):
    class Meta:
        model = popolo_models.Link
        fields = ("note", "url")


class SourceSerializer(serializers.ModelSerializer):
    class Meta:
        model = popolo_models.Source
        fields = ("note", "url")


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
    links = LinkSerializer(many=True, read_only=True)
    other_names = OtherNameSerializer(many=True, read_only=True)
    sources = SourceSerializer(many=True, read_only=True)
    images = ImageSerializer(many=True, read_only=True)

    party_sets = PartySetSerializer(many=True, read_only=True)


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

    id = serializers.ReadOnlyField(source="slug")
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
            "party",
            "party_list_position",
            "person",
            "post",
            "start_date",
            "end_date",
            "election",
        )

    elected = serializers.ReadOnlyField()
    party_list_position = serializers.ReadOnlyField()
    person = MinimalPersonSerializer(read_only=True)
    party = MinimalPartySerializer()
    post = MinimalPostSerializer(read_only=True)

    election = MinimalElectionSerializer(source="post_election.election")


class PostElectionSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = candidates_models.PostExtraElection
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
            "links",
            "memberships",
            "images",
            "thumbnail",
            "favourite_biscuit",
        )

    identifiers = IdentifierSerializer(many=True, read_only=True)
    links = LinkSerializer(many=True, read_only=True)
    other_names = OtherNameSerializer(many=True, read_only=True)
    images = ImageSerializer(many=True, read_only=True, default=[])

    versions = JSONSerializerField(read_only=True)

    memberships = MembershipSerializer(many=True, read_only=True)

    thumbnail = HyperlinkedSorlImageField(
        "300x300",
        options={"crop": "center"},
        source="primary_image",
        read_only=True,
    )


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
            "links",
            "memberships",
            "images",
            "thumbnail",
        )


class EmbeddedPostElectionSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = candidates_models.PostExtraElection
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
        many=True, read_only=True, source="postextraelection_set"
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
