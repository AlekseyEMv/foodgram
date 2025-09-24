from rest_framework.pagination import PageNumberPagination

from foodgram_backend.settings import MAX_PAGINATION_SIZE, PAGINATION_SIZE


class CustomPagination(PageNumberPagination):
    """
    Пользовательская пагинация для API.

    Предоставляет гибкую систему разбиения данных на страницы с возможностью
    настройки размера страницы через параметры запроса.

    Основные параметры:
    - page_size: размер страницы по умолчанию
    - page_size_query_param: параметр запроса для указания размера страницы
    - max_page_size: максимально допустимый размер страницы
    """
    page_size = PAGINATION_SIZE
    page_size_query_param = 'limit'
    max_page_size = MAX_PAGINATION_SIZE
