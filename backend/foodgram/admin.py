from django.contrib import admin
from django.core.exceptions import ValidationError

from foodgram.forms import (RecipeForm, IngredientRecipeForm,
                            TagRecipeForm, SubscriptionForm)
from foodgram.models import (Profile, Favorite, Ingredient,
                             IngredientRecipe, Recipe, ShoppingCart,
                             Subscription, Tag, TagRecipe)

admin.site.empty_value_display = 'Не задано'


class IngredientRecipeInline(admin.StackedInline):
    """Настройки отображения связанной модели Рецептов."""

    model = IngredientRecipe
    extra = 0
    form = IngredientRecipeForm


class TagRecipeInline(admin.StackedInline):
    """Настройки отображения связанной модели Рецептов."""

    model = TagRecipe
    extra = 0
    form = TagRecipeForm


class RecipeAdmin(admin.ModelAdmin):
    """Настройки админ панели модели Рецептов."""

    form = RecipeForm
    inlines = (
        IngredientRecipeInline,
        TagRecipeInline
    )

    list_display = (
        'name',
        'author',
        'get_favorite_count',
    )

    search_fields = ('name', 'author__username')
    list_filter = ('tags',)
    list_display_links = ('name',)

    def save_model(self, request, obj, form, change):
        obj.clean()
        super().save_model(request, obj, form, change)

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

    def save_model(self, request, obj, form, change):
        if not obj.name:
            raise ValidationError('Выберите название.')
        if not obj.measurement_unit:
            raise ValidationError('Выберите единицу измерения.')
        obj.clean()
        super().save_model(request, obj, form, change)


class TagAdmin(admin.ModelAdmin):
    """Настройки админ панели модели Тэгов."""

    list_display = (
        'name',
        'slug'
    )
    search_fields = ('slug',)
    list_display_links = ('name',)

    def save_model(self, request, obj, form, change):
        if not obj.name:
            raise ValidationError('Выберите тэги.')
        if not obj.slug:
            raise ValidationError('Выберите слаг.')
        obj.clean()
        super().save_model(request, obj, form, change)


class ProfileAdmin(admin.ModelAdmin):
    """Настройки админ панели модели Пользователя."""

    list_display = (
        'username',
        'email',
    )
    search_fields = ('email', 'username')
    list_display_links = ('username',)

    def save_model(self, request, obj, form, change):
        if not obj.username:
            raise ValidationError('Выберите юзернейм.')
        if not obj.email:
            raise ValidationError('Выберите почту.')
        obj.clean()
        super().save_model(request, obj, form, change)


class FavoriteAdmin(admin.ModelAdmin):
    """Настройки админ панели модели Избранного."""

    list_display = (
        'user',
        'recipe'
    )

    search_fields = ('user__username',)

    def save_model(self, request, obj, form, change):
        if not obj.user:
            raise ValidationError('Выберите пользователя.')
        if not obj.recipe:
            raise ValidationError('Выберите рецепт.')
        obj.clean()
        super().save_model(request, obj, form, change)


class ShoppingCartAdmin(admin.ModelAdmin):
    """Настройки админ панели модели Списка покупок."""

    list_display = (
        'user',
        'recipe',
    )

    search_fields = ('user__username',)
    list_display_links = ('user',)

    def save_model(self, request, obj, form, change):
        if not obj.user:
            raise ValidationError('Выберите пользователя.')
        if not obj.recipe:
            raise ValidationError('Выберите рецепт.')
        obj.clean()
        super().save_model(request, obj, form, change)


class SubscriptionAdmin(admin.ModelAdmin):
    """Настройки админ панели модели Подписок."""

    form = SubscriptionForm
    list_display = (
        'user',
        'subscription'
    )

    search_fields = ('user__username',)
    list_display_links = ('user',)

    def save_model(self, request, obj, form, change):
        obj.clean()
        super().save_model(request, obj, form, change)


class IngredientRecipeAdmin(admin.ModelAdmin):
    """Настройки админ панели модели Ингредиентов рецепта."""

    list_display = (
        'ingredient',
        'recipe',
        'amount',
    )

    search_fields = ('recipe__name',)
    list_display_links = ('recipe',)

    def save_model(self, request, obj, form, change):
        if not obj.ingredient:
            raise ValidationError('Выберите ингредиенты.')
        if not obj.recipe:
            raise ValidationError('Выберите рецепт.')
        if not obj.amount:
            raise ValidationError('Введите количество.')


class TagRecipeAdmin(admin.ModelAdmin):
    """Настройки админ панели модели Тэгов Рецепта."""

    list_display = (
        'tag',
        'recipe'
    )
    search_fields = ('recipe__name',)

    def save_model(self, request, obj, form, change):
        if not obj.tag:
            raise ValidationError('Выберите тэги.')
        if not obj.recipe:
            raise ValidationError('Выберите рецепт.')


admin.site.register(Recipe, RecipeAdmin)
admin.site.register(Tag, TagAdmin)
admin.site.register(Ingredient, IngredientAdmin)
admin.site.register(Profile, ProfileAdmin)
admin.site.register(Favorite, FavoriteAdmin)
admin.site.register(ShoppingCart, ShoppingCartAdmin)
admin.site.register(Subscription, SubscriptionAdmin)
admin.site.register(IngredientRecipe, IngredientRecipeAdmin)
admin.site.register(TagRecipe, TagRecipeAdmin)
