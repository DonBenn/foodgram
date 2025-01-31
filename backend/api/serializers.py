import base64

from django.contrib.auth import get_user_model
from django.core.files.base import ContentFile
from rest_framework import serializers
from rest_framework.validators import UniqueTogetherValidator
from rest_framework import status
from rest_framework.response import Response

from foodgram.constants import (MAX_AMOUNT_VALUE, MAX_COOKING_TIME_SCORE,
                                MIN_AMOUNT_VALUE, MAX_INGREDIENTS_VALUE,
                                MIN_COOKING_TIME_SCORE)
from foodgram.models import (Favorite, Ingredient, IngredientRecipe, Recipe,
                             ShoppingCart, Subscription, Tag, TagRecipe)

Profile = get_user_model()


def create_update_ingredients(recipe, ingredients):
    all_ingredients = []
    for element in ingredients:
        ingredient_id = element.get('ingredient').id
        amount_in_ingredient = element.get('amount')
        current_ingredient = Ingredient.objects.get(id=ingredient_id)
        one_ingredient = IngredientRecipe(
            ingredient=current_ingredient,
            recipe=recipe,
            amount=amount_in_ingredient
        )
        all_ingredients.append(one_ingredient)

    return IngredientRecipe.objects.bulk_create(all_ingredients)


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
        if self.context['request'].user.is_authenticated:
            return obj.subscriber.filter(subscription=obj.id).exists()
        return False


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
    name = serializers.SlugRelatedField(
        queryset=Ingredient.objects.all(), slug_field='name',
        source='ingredient'
    )
    measurement_unit = serializers.SlugRelatedField(
        queryset=Ingredient.objects.all(), slug_field='measurement_unit',
        source='ingredient'
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
    is_favorited = serializers.SerializerMethodField()
    is_in_shopping_cart = serializers.SerializerMethodField()

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

    def get_is_favorited(self, obj):
        """Метод, показывающий в избанном ли рецепт."""
        if self.context['request'].user.is_authenticated:
            user = self.context['request'].user
            return user.favorite.filter(recipe=obj.id).exists()
        return False

    def get_is_in_shopping_cart(self, obj):
        """Метод, показывающий в списке покупок ли рецепт."""
        if self.context['request'].user.is_authenticated:
            user = self.context['request'].user
            return obj.shopping_cart.filter(user=user).exists()
        return False


class CreateTagRecipeSerializer(serializers.ModelSerializer):
    """Сериалайзер создания Тэгов Рецепта."""

    id = serializers.PrimaryKeyRelatedField(
        queryset=Tag.objects.all(), source='tag'
    )

    class Meta:
        """Метаданные сериализатора Тэгов Рецепта."""

        model = TagRecipe
        fields = ('id',)


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

    def validate_id(self, value):
        """Метод валидации поля ингредиентов."""
        if not value:
            raise serializers.ValidationError(
                'Выберите ингредиенты.'
            )
        if not Ingredient.objects.filter(id=value.id).exists():
            raise serializers.ValidationError(
                'Нет такого ингредиента.'
            )
        return value

    def validate_amount(self, value):
        """Метод валидации поля ингредиентов."""
        if int(value) > MAX_AMOUNT_VALUE:
            raise serializers.ValidationError(
                'Слишком большое колличество.'
            )
        if int(value) < MIN_AMOUNT_VALUE:
            raise serializers.ValidationError(
                'Слишком маленькое колличество.'
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
        for element in value:
            if not Tag.objects.filter(id=element.id).exists():
                raise serializers.ValidationError(
                    'Нет такого тега.'
                )
        return value

    def validate_ingredients(self, value):
        """Метод валидации поля ингредиентов."""
        if not value:
            raise serializers.ValidationError(
                'Выберите ингредиенты.'
            )
        if len(value) > MAX_INGREDIENTS_VALUE:
            raise serializers.ValidationError(
                'Слишком много игредиентов.'
            )
        return value

    def validate(self, data):
        """Метод валидации данных добавления отзыва."""
        if not data.get('tags'):
            raise serializers.ValidationError(
                'Нельзя редактировать рецепт без тегов'
            )
        if not data.get('ingredient_recipe'):
            raise serializers.ValidationError(
                'Нельзя редактировать рецепт без ингредиентов'
            )
        return data

    def validate_cooking_time(self, value):
        """Метод валидации поля время приготовления."""
        if value < MIN_COOKING_TIME_SCORE:
            raise serializers.ValidationError(
                'Слишком мало минут.'
            )
        if value > MAX_COOKING_TIME_SCORE:
            raise serializers.ValidationError(
                'Слишком много минут.'
            )
        return value

    def create(self, validated_data):
        """Метод создания рецепта."""
        author = self.context['request'].user
        data_name = validated_data.get('name')
        data_text = validated_data.get('text')
        data_cooking_time = validated_data.get('cooking_time')
        recipe_exists = Recipe.objects.filter(
            author=author,
            name=data_name,
            text=data_text,
            cooking_time=data_cooking_time
        )
        if recipe_exists:
            return Response(
                'Уже есть такой рецепт',
                status=status.HTTP_400_BAD_REQUEST
            )
        validated_data['author'] = author
        ingredients = validated_data.pop('ingredient_recipe')
        tags = validated_data.pop('tags')

        recipe = Recipe.objects.create(**validated_data)
        create_update_ingredients(recipe, ingredients)
        recipe.tags.set(tags)
        return recipe

    def update(self, recipe, validated_data):
        """Метод обновления рецепта."""
        ingredients = validated_data.pop('ingredient_recipe')
        tags = validated_data.pop('tags')
        super().update(recipe, validated_data)

        recipe.ingredient_recipe.all().delete()
        create_update_ingredients(recipe, ingredients)
        recipe.tag_recipe.all().delete()
        recipe.tags.set(tags)

        recipe.save()
        return recipe

    def to_representation(self, instance):
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
    id = serializers.ReadOnlyField(source='subscription.id')
    username = serializers.ReadOnlyField(source='subscription.username')
    email = serializers.ReadOnlyField(source='subscription.email')
    first_name = serializers.ReadOnlyField(source='subscription.first_name')
    last_name = serializers.ReadOnlyField(source='subscription.last_name')
    is_subscribed = serializers.SerializerMethodField()
    recipes_count = serializers.SerializerMethodField()
    recipes = serializers.SerializerMethodField()
    avatar = serializers.ImageField(
        source='subscription.avatar', read_only=True
    )

    class Meta:
        """Метаданные сериализатора создания подписак пользователя."""

        model = Subscription
        fields = (
            'user',
            'subscription',
            'id',
            'username',
            'email',
            'first_name',
            'last_name',
            'is_subscribed',
            'avatar',
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

    def get_is_subscribed(self, obj):
        """Метод, подписанн ли пользователь."""
        return obj.user.subscriber.filter(
            subscription=obj.subscription_id
        ).exists()

    def to_representation(self, instance):
        data = super().to_representation(instance)
        data.pop('user')
        data.pop('subscription')
        return data


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
        serializer = RecipeMinifiedSerializer(obj.recipes, many=True)
        return serializer.data
