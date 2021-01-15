from rest_framework import pagination


class DefaultPageNumberPagination(pagination.PageNumberPagination):
    page_size = 10
    page_size_query_param = "page_size"
    max_page_size = 200
