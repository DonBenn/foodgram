from rest_framework.pagination import LimitOffsetPagination

from foodgram.constants import MAX_PAGE_SIZE_IN_REQUEST, MAX_PAGE_SIZE


class LimitNumberPaginator(LimitOffsetPagination):
    """Пагинатор для вьюсета Рецепта."""
    page_size_query_param = 'limit'


class LimitSubscriptionsPaginator(LimitOffsetPagination):
    """Пагинатор для вьюсета Подписок."""
    page_size = MAX_PAGE_SIZE_IN_REQUEST
    page_size_query_param = 'limit'
    max_page_size = MAX_PAGE_SIZE
