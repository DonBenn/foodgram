from django_filters import AllValuesMultipleFilter
from django_filters import rest_framework as filters
from rest_framework.filters import SearchFilter

from foodgram.models import Recipe


class IngredientFilter(SearchFilter):
    """Настройки фильтра Ингредиентов."""

    search_param = 'name'


class RecipeFilter(filters.FilterSet):
    """Настройки фильтра Рецептов."""

    tags = AllValuesMultipleFilter(field_name='tags__slug')
    is_favorited = filters.BooleanFilter(method='filter_is_favorited')
    is_in_shopping_cart = filters.BooleanFilter(
        method='filter_is_in_shopping_cart'
    )

    class Meta:
        model = Recipe
        fields = [
            'author',
            'tags',
            'is_in_shopping_cart',
            'is_favorited'
        ]

    def filter_is_favorited(self, queryset, name, value):
        """Метод фильтрации, в избранных ли рецепт."""
        if not self.request.user.is_authenticated:
            return queryset.none()

        if value:
            return queryset.filter(favorite__user=self.request.user)

    def filter_is_in_shopping_cart(self, queryset, name, value):
        """Метод фильтрации, в списке покупок ли рецепт."""
        if not self.request.user.is_authenticated:
            return queryset.none()

        if value:
            return queryset.filter(shopping_cart__user=self.request.user)
