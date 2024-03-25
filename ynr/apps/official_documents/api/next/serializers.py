from official_documents.models import BallotSOPN
from rest_framework import serializers


class BallotSOPNSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = BallotSOPN
        fields = ("uploaded_file", "source_url")
        ref_name = None  # Tells swagger that this is always embedded
