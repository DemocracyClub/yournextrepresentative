import json

from rest_framework import pagination, serializers


class DefaultPageNumberPagination(pagination.PageNumberPagination):
    page_size = 10
    page_size_query_param = "page_size"
    max_page_size = 200


class JSONSerializerField(serializers.Field):
    def to_representation(self, value):
        if value:
            return json.loads(value)
