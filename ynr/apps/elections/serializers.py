from rest_framework import serializers

from api.next.serializers import OrganizationSerializer
from candidates import models as candidates_models
from elections import models as election_models
from official_documents.serializers import OfficialDocumentSerializer


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

    organization = OrganizationSerializer(read_only=True)


class PostElectionSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = candidates_models.Ballot
        fields = (
            "id",
            "url",
            "election",
            "winner_count",
            "ballot_paper_id",
            "cancelled",
            "sopn",
        )

    election = MinimalElectionSerializer(read_only=True)
    sopn = OfficialDocumentSerializer(read_only=True)


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
