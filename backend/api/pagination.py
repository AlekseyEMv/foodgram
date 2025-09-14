from rest_framework.pagination import PageNumberPagination

from foodgram_backend.settings import MAX_PAGINATION_SIZE, PAGINATION_SIZE


class CustomPagination(PageNumberPagination):
    page_size = PAGINATION_SIZE
    page_size_query_param = 'limit'
    max_page_size = MAX_PAGINATION_SIZE
