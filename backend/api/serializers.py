import base64

from django.core.files.base import ContentFile
from rest_framework import serializers
from rest_framework.validators import UniqueTogetherValidator

from foodgram.constants import (MAX_AMOUNT_VALUE, MAX_COOKING_TIME_SCORE,
                                MIN_AMOUNT_VALUE, MIN_COOKING_TIME_SCORE)
from foodgram.models import (Favorite, Ingredient, IngredientRecipe, Recipe,
                             ShoppingCart, Subscription, Tag, Profile)


class Base64ImageField(serializers.ImageField):
    """Сериалайзер изображения"""

    def to_internal_value(self, data):
        """Метод декодирования изображения."""
        if isinstance(data, str) and data.startswith('data:image'):
            format, imgstr = data.split(';base64,')
            ext = format.split('/')[-1]
            data = ContentFile(base64.b64decode(imgstr), name='temp.' + ext)
        return super().to_internal_value(data)


class AvatarSeializer(serializers.ModelSerializer):
    """Сериалайзер изображения аватора."""

    avatar = Base64ImageField(allow_null=True)

    class Meta:
        """Метаданные сериализатора аватора."""

        model = Profile
        fields = ('avatar',)

    def update(self, user, data):
        """Метод обновления аватора."""
        user.avatar = data.get('avatar')
        user.save()
        return user


class UserListSerializer(serializers.ModelSerializer):
    """Сериалайзер данных пользователя"""

    is_subscribed = serializers.SerializerMethodField()

    class Meta:
        """Метаданные сериализатора пользователя."""

        model = Profile
        fields = (
            'id',
            'username',
            'email',
            'first_name',
            'last_name',
            'is_subscribed',
            'avatar',
        )

    def get_is_subscribed(self, obj):
        """Метод, подписан ли пользователь."""
        return self.context['request'].user.is_authenticated and (
            self.context['request'].user.subscriber.filter(
                subscription=obj.id).exists()
        )


class TagSerializer(serializers.ModelSerializer):
    """Сериалайзер Тэгов."""

    class Meta:
        """Метаданные сериализатора Тэгов."""

        model = Tag
        fields = '__all__'


class IgredientRecipeSerializer(serializers.ModelSerializer):
    """Сериалайзер Ингредиентов и Количества."""

    id = serializers.PrimaryKeyRelatedField(
        queryset=Ingredient.objects.all(), source='ingredient'
    )
    name = serializers.ReadOnlyField(source='ingredient.name')
    measurement_unit = serializers.ReadOnlyField(
        source='ingredient.measurement_unit'
    )
    amount = serializers.IntegerField()

    class Meta:
        """Метаданные сериализатора Ингредиентов и Количества."""

        model = IngredientRecipe
        fields = ('id', 'name', 'measurement_unit', 'amount')


class IngredientSerializer(serializers.ModelSerializer):
    """Сериалайзер Ингредиентов."""

    class Meta:
        """Метаданные сериализатора Ингредиентов."""

        model = Ingredient
        fields = '__all__'


class RecipeSerializer(serializers.ModelSerializer):
    """Сериалайзер Рецепта."""

    author = UserListSerializer()
    tags = TagSerializer(many=True)
    ingredients = IgredientRecipeSerializer(
        many=True, source='ingredient_recipe'
    )
    is_favorited = serializers.BooleanField(default=False)
    is_in_shopping_cart = serializers.BooleanField(default=False)

    class Meta:
        """Метаданные сериализатора Рецепта."""

        model = Recipe
        fields = (
            'id',
            'author',
            'is_favorited',
            'is_in_shopping_cart',
            'ingredients',
            'tags',
            'image',
            'name',
            'text',
            'cooking_time'
        )


class CreateIgredientRecipeSerializer(serializers.ModelSerializer):
    """Сериалайзер Ингредиентов и Количества."""

    id = serializers.PrimaryKeyRelatedField(
        queryset=Ingredient.objects.all(), source='ingredient'
    )
    amount = serializers.IntegerField()

    class Meta:
        """Метаданные сериализатора Ингредиентов и Количества."""

        model = IngredientRecipe
        fields = ('id', 'amount')

    def validate_amount(self, value):
        """Метод валидации поля ингредиентов."""
        if value < MIN_AMOUNT_VALUE or value > MAX_AMOUNT_VALUE:
            raise serializers.ValidationError(
                'Выберете колличество от 1 до 20000.'
            )
        return value


class RecipeCreateSerializer(serializers.ModelSerializer):
    """Сериалайзер создания Рецепта."""

    tags = serializers.PrimaryKeyRelatedField(
        many=True, queryset=Tag.objects.all(), required=True
    )
    ingredients = CreateIgredientRecipeSerializer(
        many=True, source='ingredient_recipe', required=True
    )
    image = Base64ImageField(required=True)
    cooking_time = serializers.IntegerField(required=True)

    class Meta:
        """Метаданные сериализатора создания Рецепта."""

        model = Recipe
        fields = (
            'ingredients',
            'tags',
            'image',
            'name',
            'text',
            'cooking_time'
        )

    def validate_tags(self, value):
        """Метод валидации поля тэгов."""
        if not value:
            raise serializers.ValidationError(
                'Выберите теги.'
            )
        unique_tags = set(value)
        if len(value) > len(unique_tags):
            raise serializers.ValidationError(
                'Нельзя выбрать один тэг два раза.'
            )
        return value

    def validate_ingredients(self, value):
        """Метод валидации поля ингредиентов."""
        if not value:
            raise serializers.ValidationError(
                'Выберите ингредиенты.'
            )
        ingredients = list(value)
        unique_ingredients = []

        for ingredient in ingredients:
            if ingredient not in unique_ingredients:
                unique_ingredients.append(ingredient)

        if len(ingredients) != len(unique_ingredients):
            raise serializers.ValidationError(
                'Нельзя выбрать один ингредиент два раза.'
            )
        return value

    def validate_cooking_time(self, value):
        """Метод валидации поля время приготовления."""
        if value < MIN_COOKING_TIME_SCORE or value > MAX_COOKING_TIME_SCORE:
            raise serializers.ValidationError(
                'Выберете от 1 до 1000 минут.'
            )
        return value

    def create_update_ingredients(self, recipe, ingredients):
        """Метод создания удаления ингредиентов."""
        all_ingredients = []
        for element in ingredients:
            current_ingredient = element.get('ingredient')
            amount_in_ingredient = element.get('amount')
            one_ingredient = IngredientRecipe(
                ingredient=current_ingredient,
                recipe=recipe,
                amount=amount_in_ingredient
            )
            all_ingredients.append(one_ingredient)

        return IngredientRecipe.objects.bulk_create(all_ingredients)

    def create(self, validated_data):
        """Метод создания рецепта."""
        author = self.context['request'].user
        validated_data['author'] = author
        ingredients = validated_data.pop('ingredient_recipe')
        tags = validated_data.pop('tags')
        recipe = super().create(validated_data)
        self.create_update_ingredients(recipe, ingredients)
        recipe.tags.set(tags)
        return recipe

    def update(self, recipe, validated_data):
        """Метод обновления рецепта."""
        ingredients = validated_data.pop('ingredient_recipe')
        tags = validated_data.pop('tags')
        super().update(recipe, validated_data)
        recipe.ingredient_recipe.all().delete()
        self.create_update_ingredients(recipe, ingredients)
        recipe.tag_recipe.all().delete()
        recipe.tags.set(tags)
        recipe.save()
        return recipe

    def to_representation(self, instance):
        """Метод представления рецепта."""
        serializer = RecipeSerializer(
            instance, context={'request': self.context['request']}
        )
        return serializer.data


class AddRecipeSerializer(serializers.ModelSerializer):
    """Общий Сериалайзер добавления Рецепта."""

    recipe = serializers.PrimaryKeyRelatedField(queryset=Recipe.objects.all())
    user = serializers.SlugRelatedField(
        default=serializers.CurrentUserDefault(),
        slug_field='username', queryset=Profile.objects.all()
    )

    class Meta:
        """Метаданные сериализатора добавления Рецепта."""

        fields = ('recipe', 'user')

    def to_representation(self, instance):
        """Метод представления добавления рецепта."""
        serializer = RecipeMinifiedSerializer(instance.recipe)
        return serializer.data


class FavoriteCreateSerializer(AddRecipeSerializer):
    """Сериалайзер добавления в Избанное."""

    class Meta(AddRecipeSerializer.Meta):
        """Метаданные сериализатора добавления в Избанное."""

        model = Favorite
        validators = [
            UniqueTogetherValidator(
                queryset=Favorite.objects.all(),
                fields=('user', 'recipe')
            )
        ]


class ShoppingCartSerializer(AddRecipeSerializer):
    """Сериалайзер Списка покупок."""

    class Meta(AddRecipeSerializer.Meta):
        """Метаданные сериализатора Списка покупок."""

        model = ShoppingCart
        validators = [
            UniqueTogetherValidator(
                queryset=ShoppingCart.objects.all(),
                fields=('user', 'recipe')
            )
        ]


class RecipeMinifiedSerializer(serializers.ModelSerializer):
    """Сериалайзер сокращённых данных рецепта."""

    class Meta:
        """Метаданные сериализатора."""

        model = Recipe
        fields = (
            'id',
            'name',
            'image',
            'cooking_time'
        )


class SubscriptionCreateSerializer(serializers.ModelSerializer):
    """Сериалайзер создания подписак пользователя."""

    user = serializers.PrimaryKeyRelatedField(
        queryset=Profile.objects.all()
    )
    subscription = serializers.PrimaryKeyRelatedField(
        queryset=Profile.objects.all()
    )
    recipes_count = serializers.SerializerMethodField()
    recipes = serializers.SerializerMethodField()

    class Meta:
        """Метаданные сериализатора создания подписак пользователя."""

        model = Subscription
        fields = (
            'user',
            'subscription',
            'recipes_count',
            'recipes',
        )
        validators = [
            UniqueTogetherValidator(
                queryset=Subscription.objects.all(),
                fields=('user', 'subscription')
            )
        ]

    def validate_subscription(self, value):
        """Метод валидации поля подписок."""
        if self.context['request'].user == value:
            raise serializers.ValidationError(
                'Нельзя подписаться на самого себя.'
            )
        return value

    def get_recipes_count(self, obj):
        """Метод подсчёта количесва рецептов."""
        return obj.subscription.recipes.count()

    def get_recipes(self, obj):
        """Метод отображения сокращённой информации рецепта."""
        recipes = obj.subscription.recipes.all()
        serializer = RecipeMinifiedSerializer(recipes, many=True)
        return serializer.data

    def to_representation(self, instance):
        """Метод представления создания подписок."""
        data = super().to_representation(instance)
        all_recipes = data.pop('recipes')

        if self.context['request'].query_params:
            if 'recipes_limit' in self.context['request'].query_params:
                recipes_limit = self.context['request'].query_params.get(
                    'recipes_limit'
                )
                all_recipes = all_recipes[:int(recipes_limit)]

        serializer = UserListSerializer(
            instance.subscription, context={'request': self.context['request']}
        )
        subscription = serializer.data
        subscription['recipes_count'] = data.pop('recipes_count')
        subscription['recipes'] = all_recipes
        return subscription


class SubscriptionSerializer(UserListSerializer):
    """Сериалайзер подписак пользователя."""

    recipes_count = serializers.SerializerMethodField()
    recipes = serializers.SerializerMethodField()

    class Meta(UserListSerializer.Meta):
        """Метаданные сериализатора подписак пользователя."""

        model = Profile
        fields = UserListSerializer.Meta.fields + (
            'recipes', 'recipes_count'
        )

    def get_recipes_count(self, obj):
        """Метод подсчёта количесва рецептов."""
        return obj.recipes.count()

    def get_recipes(self, obj):
        """Метод отображения сокращённой информации рецепта."""
        recipes = obj.recipes.all()
        if self.context['request'].query_params:
            if 'recipes_limit' in self.context['request'].query_params:
                recipes_limit = self.context['request'].query_params.get(
                    'recipes_limit'
                )
                recipes = recipes[:int(recipes_limit)]
        serializer = RecipeMinifiedSerializer(recipes, many=True)
        return serializer.data
