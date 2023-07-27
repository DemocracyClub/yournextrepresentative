from official_documents.models import OfficialDocument
from rest_framework import serializers


class OfficialDocumentSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = OfficialDocument
        fields = ("document_type", "uploaded_file", "source_url")
