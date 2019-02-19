from rest_framework import serializers

from official_documents.models import OfficialDocument


class OfficialDocumentSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = OfficialDocument
        fields = (
            "document_type",
            "uploaded_file",
            "post_election",
            "source_url",
        )
