from django import forms

from foodgram.models import (Recipe, Ingredient, IngredientRecipe,
                             TagRecipe, Tag, Subscription)
from foodgram.constants import (MAX_AMOUNT_VALUE, MIN_AMOUNT_VALUE,
                                MIN_COOKING_TIME_SCORE, MAX_COOKING_TIME_SCORE)


class TagRecipeForm(forms.ModelForm):
    """Форма модели Тэгов рецепта."""

    class Meta:
        model = TagRecipe
        fields = ['tag']

    def clean(self):
        cleaned_data = super().clean()
        tag = cleaned_data.get('tag')
        if not tag:
            self.add_error('tag', 'Выберите теги.')

        if not Tag.objects.filter(id=tag.id).exists():
            self.add_error('tag', 'Нет такого тега.')


class IngredientRecipeForm(forms.ModelForm):
    """Форма модели Ингредиентов рецепта."""

    class Meta:
        model = IngredientRecipe
        fields = ['ingredient', 'amount']

    def clean(self):
        cleaned_data = super().clean()
        ingredient = cleaned_data.get('ingredient')
        amount = cleaned_data.get('amount')

        if not ingredient:
            self.add_error('ingredient', 'Рецепт должен содержать ингредиент.')
        if not amount:
            self.add_error('amount', 'Ингредиент должен содержать количество.')

        if not Ingredient.objects.filter(id=ingredient.id).exists():
            self.add_error('ingredient', 'Нет такого ингредиента.')

        if amount not in range(MIN_AMOUNT_VALUE, MAX_AMOUNT_VALUE):
            self.add_error(
                'amount',
                f'Выберете диапозон колличества от {MIN_AMOUNT_VALUE} до'
                f' {MAX_AMOUNT_VALUE}.'
            )

        return cleaned_data


class RecipeForm(forms.ModelForm):
    """Форма модели Рецепта."""

    class Meta:
        model = Recipe
        fields = (
            'image',
            'author',
            'name',
            'text',
            'cooking_time',
            'tags',
        )

    def clean(self):
        cleaned_data = super().clean()
        cooking_time = cleaned_data.get('cooking_time')

        if cooking_time not in range(
            MIN_COOKING_TIME_SCORE, MAX_COOKING_TIME_SCORE
        ):
            self.add_error(
                'cooking_time',
                f'Выберете диапазон от {MIN_COOKING_TIME_SCORE}'
                f'до {MAX_COOKING_TIME_SCORE} минут.'
            )


class SubscriptionForm(forms.ModelForm):
    """Форма модели Подписок."""

    class Meta:
        model = Subscription
        fields = ['user', 'subscription']

    def clean(self):
        cleaned_data = super().clean()
        user = cleaned_data.get('user')
        subscription = cleaned_data.get('subscription')

        if user == subscription:
            self.add_error('subscription', 'Нельзя подписаться на себя.')
