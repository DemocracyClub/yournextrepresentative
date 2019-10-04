from rest_framework import serializers

from api.next.serializers import OrganizationSerializer
from candidates import models as candidates_models
from elections import models as election_models
from official_documents.serializers import OfficialDocumentSerializer
from popolo.serializers import NominationAndResultSerializer
from utils.db import LastWord


class MinimalElectionSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = election_models.Election
        fields = ("election_id", "url", "name", "election_date")

    election_id = serializers.ReadOnlyField(source="slug")

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


class BallotSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = candidates_models.Ballot
        fields = (
            "url",
            "election",
            "winner_count",
            "ballot_paper_id",
            "cancelled",
            "sopn",
            "candidates_locked",
            "candidates",
        )

    url = serializers.HyperlinkedIdentityField(
        view_name="ballot-detail",
        lookup_field="ballot_paper_id",
        lookup_url_kwarg="ballot_paper_id",
    )

    election = MinimalElectionSerializer(read_only=True)
    sopn = OfficialDocumentSerializer(read_only=True)
    candidates = serializers.SerializerMethodField()

    def get_candidates(self, instance):
        qs = (
            instance.membership_set.all()
            .select_related("result", "person", "party")
            .annotate(last_name=LastWord("person__name"))
        )

        order_by = ["-elected", "-result__is_winner", "-result__num_ballots"]
        if instance.election.party_lists_in_use:
            order_by += ["party__name", "party_list_position"]
        else:
            order_by += ["person__sort_name", "last_name"]
        qs = qs.order_by(*order_by)

        return NominationAndResultSerializer(qs, many=True).data


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
    url = serializers.HyperlinkedIdentityField(
        view_name="ballot-detail",
        lookup_field="ballot_paper_id",
        lookup_url_kwarg="ballot_paper_id",
    )
