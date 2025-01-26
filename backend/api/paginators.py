from rest_framework.pagination import LimitOffsetPagination


class LimitNumberPaginator(LimitOffsetPagination):
    """Пагинатор для вьюсета Рецепта."""
    page_size_query_param = 'limit'


class LimitSubscriptionsPaginator(LimitOffsetPagination):
    """Пагинатор для вьюсета Подписок."""
    page_size = 10
    page_size_query_param = 'limit'
    max_page_size = 20
