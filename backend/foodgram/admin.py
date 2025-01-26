from django.contrib import admin
from foodgram.models import (CustomUser, Favorite, Ingredient,
                             IngredientRecipe, Recipe, ShoppingCart,
                             Subscription, Tag, TagRecipe)

admin.site.empty_value_display = 'Не задано'


class RecipeAdmin(admin.ModelAdmin):
    """Настройки админ панели модели Рецептов."""

    list_display = (
        'name',
        'author',
        'get_favorite_count',
    )

    search_fields = ('name', 'author__username')
    list_filter = ('tags',)
    list_display_links = ('name',)

    def get_favorite_count(self, obj):
        """Функция подсчёта колличества избанного у рецепта."""
        return obj.get_favorite_count()


class IngredientAdmin(admin.ModelAdmin):
    """Настройки админ панели модели Ингредиентов."""

    list_display = (
        'name',
        'measurement_unit'
    )

    search_fields = ('name',)
    list_display_links = ('name',)


class TagAdmin(admin.ModelAdmin):
    """Настройки админ панели модели Тэгов."""

    list_display = (
        'name',
        'slug'
    )
    search_fields = ('slug',)
    list_display_links = ('name',)


class CustomUserAdmin(admin.ModelAdmin):
    """Настройки админ панели модели Пользователя."""

    list_display = (
        'username',
        'email',
    )
    search_fields = ('email', 'username')
    list_display_links = ('username',)


class FavoriteAdmin(admin.ModelAdmin):
    """Настройки админ панели модели Избранного."""

    list_display = (
        'user',
        'recipe'
    )

    search_fields = ('user__username',)


class ShoppingCartAdmin(admin.ModelAdmin):
    """Настройки админ панели модели Списка покупок."""

    list_display = (
        'user',
        'recipe',
        'ingredient',
        'amount',
    )

    search_fields = ('user__username',)
    list_display_links = ('user',)


class SubscriptionAdmin(admin.ModelAdmin):
    """Настройки админ панели модели Подписок."""

    list_display = (
        'user',
        'subscription'
    )

    search_fields = ('user__username',)
    list_display_links = ('user',)


class IngredientRecipeAdmin(admin.ModelAdmin):
    """Настройки админ панели модели Ингредиентов рецепта."""

    list_display = (
        'ingredient',
        'recipe',
        'amount',
    )

    search_fields = ('recipe__name',)
    list_display_links = ('recipe',)


class TagRecipeAdmin(admin.ModelAdmin):
    """Настройки админ панели модели Тэгов Рецепта."""

    list_display = (
        'tag',
        'recipe'
    )
    search_fields = ('recipe__name',)


admin.site.register(Recipe, RecipeAdmin)
admin.site.register(Tag, TagAdmin)
admin.site.register(Ingredient, IngredientAdmin)
admin.site.register(CustomUser, CustomUserAdmin)
admin.site.register(Favorite, FavoriteAdmin)
admin.site.register(ShoppingCart, ShoppingCartAdmin)
admin.site.register(Subscription, SubscriptionAdmin)
admin.site.register(IngredientRecipe, IngredientRecipeAdmin)
admin.site.register(TagRecipe, TagRecipeAdmin)
