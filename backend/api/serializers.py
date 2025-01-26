import base64

from django.contrib.auth import get_user_model
from django.core.files.base import ContentFile
from foodgram.constants import (MAX_AMOUNT_VALUE, MAX_COOKING_TIME_VALUE,
                                MAX_INGREDIENTS_VALUE)
from foodgram.models import (Favorite, Ingredient, IngredientRecipe, Recipe,
                             ShoppingCart, Subscription, Tag, TagRecipe)
from rest_framework import serializers
from rest_framework.validators import UniqueTogetherValidator

CustomUser = get_user_model()


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

        model = CustomUser
        fields = ('avatar',)

    def update(self, user, data):
        """Метод обновления аватора."""
        user = CustomUser.objects.get(id=user.id)
        user.avatar = data.get('avatar')
        user.save()
        return user


class UserListSerializer(serializers.ModelSerializer):
    """Сериалайзер данных пользователя"""

    is_subscribed = serializers.SerializerMethodField()

    class Meta:
        """Метаданные сериализатора пользователя."""

        model = CustomUser
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
        author = self.context['request'].user
        if not author.is_authenticated:
            return False
        return Subscription.objects.filter(
            subscription=obj.id,
            user=author
        ).exists()


class TagSerializer(serializers.ModelSerializer):
    """Сериалайзер Тэгов."""

    class Meta:
        """Метаданные сериализатора Тэгов."""

        model = Tag
        fields = '__all__'


class IgredientAmountSerializer(serializers.ModelSerializer):
    """Сериалайзер Ингредиентов и Количества."""

    amount = serializers.SerializerMethodField()

    class Meta:
        """Метаданные сериализатора Ингредиентов и Количества."""

        model = Ingredient
        fields = ('id', 'name', 'measurement_unit', 'amount')

    def get_amount(self, obj):
        """Метод подсчёта Количества ингредиента."""
        if self.context.get('request'):
            if self.context['request'].method == 'PATCH':
                if self.context.get('view'):
                    recipe = self.context['view'].kwargs['pk']
                else:
                    recipe = self.context.get('recipe')
            else:
                recipe = self.context.get('recipe')
        else:
            recipe = self.context.get('recipe')
        ingredient_recipe = IngredientRecipe.objects.get(
            ingredient=obj.id,
            recipe=recipe
        )
        return ingredient_recipe.amount


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
    ingredients = IgredientAmountSerializer(many=True)
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
            favorited_recipe = Favorite.objects.filter(
                recipe=obj.id,
                user=user
            ).exists()
            return favorited_recipe
        else:
            return False

    def get_is_in_shopping_cart(self, obj):
        """Метод, показывающий в списке покупок ли рецепт."""
        if self.context['request'].user.is_authenticated:
            user = self.context['request'].user
            in_shopping_cart = obj.shopping_cart.filter(user=user).exists()
            return in_shopping_cart
        return False


class RecipeCreateSerializer(serializers.ModelSerializer):
    """Сериалайзер создания Рецепта."""

    tags = serializers.ListField(
        child=serializers.IntegerField(write_only=True),
        write_only=True,
        required=True
    )
    ingredients = serializers.ListField(write_only=True, required=True)
    image = Base64ImageField(required=True)

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
            if not Tag.objects.filter(id=element).exists():
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
        for element in value:
            if not Ingredient.objects.filter(id=element.get('id')).exists():
                raise serializers.ValidationError(
                    'Нет такого ингредиента.'
                )
            if int(element.get('amount')) > MAX_AMOUNT_VALUE:
                raise serializers.ValidationError(
                    'Слишком большое колличество.'
                )
        if len(value) > MAX_INGREDIENTS_VALUE:
            raise serializers.ValidationError(
                'Слишком много игредиентов.'
            )
        return value

    def validate_cooking_time(self, value):
        """Метод валидации поля время приготовления."""
        if not value:
            raise serializers.ValidationError(
                'Введите время приготовления'
            )
        if value > MAX_COOKING_TIME_VALUE:
            raise serializers.ValidationError(
                'Слишком много минут.'
            )
        return value

    def create(self, validated_data):
        """Метод создания рецепта."""
        ingredients = validated_data.pop('ingredients')
        tags = validated_data.pop('tags')
        recipe = Recipe.objects.create(**validated_data)

        all_ingredients = []
        for element in ingredients:
            ingredient_id = element.get('id')
            amount_in_ingredient = element.get('amount')
            current_ingredient = Ingredient.objects.get(id=ingredient_id)
            one_ingredient = IngredientRecipe(
                ingredient=current_ingredient,
                recipe=recipe,
                amount=amount_in_ingredient
            )
            all_ingredients.append(one_ingredient)
        IngredientRecipe.objects.bulk_create(all_ingredients)

        all_tags = []
        for tag in tags:
            current_tag = Tag.objects.get(id=tag)
            one_tag = TagRecipe(tag=current_tag, recipe=recipe)
            all_tags.append(one_tag)
        TagRecipe.objects.bulk_create(all_tags)
        return recipe

    def update(self, request, data):
        """Метод обновления рецепта."""
        recipe = Recipe.objects.get(id=request.id)
        recipe.name = data.get('name')
        recipe.text = data.get('text')
        recipe.image = data.get('image')
        recipe.cooking_time = data.get('cooking_time')
        ingredients = data.get('ingredients')
        tags = data.get('tags')
        recipe.ingredientrecipe.all().delete()

        all_ingredients = []
        for element in ingredients:
            ingredient_id = element.get('id')
            amount_in_ingredient = element.get('amount')
            current_ingredient = Ingredient.objects.get(id=ingredient_id)
            one_ingredient = IngredientRecipe(
                ingredient=current_ingredient,
                recipe=recipe,
                amount=amount_in_ingredient
            )
            all_ingredients.append(one_ingredient)
        IngredientRecipe.objects.bulk_create(all_ingredients)

        recipe.tagrecipe_set.all().delete()
        all_tags = []
        for tag in tags:
            current_tag = Tag.objects.get(id=tag)
            one_tag = TagRecipe(tag=current_tag, recipe=recipe)
            all_tags.append(one_tag)
        TagRecipe.objects.bulk_create(all_tags)

        recipe.save()
        return recipe


class FavoriteCreateSerializer(serializers.ModelSerializer):
    """Сериалайзер добавления в Избанное."""

    recipe = serializers.PrimaryKeyRelatedField(queryset=Recipe.objects.all())
    user = serializers.SlugRelatedField(
        default=serializers.CurrentUserDefault(),
        slug_field='username', queryset=CustomUser.objects.all()
    )

    class Meta:
        """Метаданные сериализатора добавления в Избанное."""

        model = Favorite
        fields = ('recipe', 'user')

    def validate(self, data):
        """Метод валидации полей добавления в избранное."""
        author = data.get('user')
        recipe = data.get('recipe')
        if author.favorite.filter(recipe=recipe):
            raise serializers.ValidationError(
                'Вы уже добавили этот рецепт в избранное.'
            )
        return data


class ShoppingCartSerializer(serializers.ModelSerializer):
    """Сериалайзер Списка покупок."""

    recipe = serializers.PrimaryKeyRelatedField(queryset=Recipe.objects.all())
    user = serializers.SlugRelatedField(
        default=serializers.CurrentUserDefault(),
        slug_field='username', queryset=CustomUser.objects.all()
    )

    class Meta:
        """Метаданные сериализатора Списка покупок."""

        model = ShoppingCart
        fields = ('recipe', 'user')

    def validate(self, data):
        """Метод валидации полей Списка покупок."""
        author = data.get('user')
        recipe = data.get('recipe')
        if author.shopping_cart.filter(recipe=recipe):
            raise serializers.ValidationError(
                'Вы уже добавили этот рецепт в корзину.'
            )
        return data

    def create(self, validated_data):
        """Метод создания списка покупок."""
        user = validated_data['user']
        recipe = validated_data.get('recipe')
        ingredients = recipe.ingredients.all()

        all_ingredients = []
        for element in ingredients:
            ingredient_id = element.id
            ingredient_recipe = IngredientRecipe.objects.get(
                recipe=recipe,
                ingredient=ingredient_id
            )
            current_ingredient = Ingredient.objects.get(id=ingredient_id)
            one_ingredient = ShoppingCart(
                ingredient=current_ingredient,
                recipe=recipe,
                user=user,
                amount=ingredient_recipe.amount
            )
            all_ingredients.append(one_ingredient)
        shopping_cart = ShoppingCart.objects.bulk_create(all_ingredients)
        return shopping_cart


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
        queryset=CustomUser.objects.all()
    )
    subscription = serializers.PrimaryKeyRelatedField(
        queryset=CustomUser.objects.all()
    )

    class Meta:
        """Метаданные сериализатора создания подписак пользователя."""

        model = Subscription
        fields = ('user', 'subscription')
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

    def validate(self, data):
        """Метод валидации полей сериализатора."""
        author = data.get('user')
        subscription = data.get('subscription')
        if self.context['request'].method == 'POST':
            if author.subscriber.filter(subscription=subscription):
                raise serializers.ValidationError(
                    'Вы уже подписались на этого автора.'
                )
        return data


class SubscriptionSerializer(serializers.ModelSerializer):
    """Сериалайзер подписак пользователя."""

    recipes_count = serializers.SerializerMethodField()
    recipes = serializers.SerializerMethodField()
    is_subscribed = serializers.SerializerMethodField()
    id = serializers.SerializerMethodField()
    username = serializers.SerializerMethodField()
    email = serializers.SerializerMethodField()
    first_name = serializers.SerializerMethodField()
    last_name = serializers.SerializerMethodField()
    avatar = serializers.SerializerMethodField()

    class Meta:
        """Метаданные сериализатора подписак пользователя."""

        model = CustomUser
        fields = (
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

    def get_recipes_count(self, obj):
        """Метод подсчёта количесва рецептов."""
        if self.context['request'].method == 'POST':
            return Recipe.objects.filter(author=obj.id).count()
        return Recipe.objects.filter(author=obj.subscription_id).count()

    def get_recipes(self, obj):
        """Метод отображения сокращённой информации рецепта."""
        if self.context['request'].method == 'POST':
            recipes = Recipe.objects.filter(author=obj.id)
            serializer = RecipeMinifiedSerializer(recipes, many=True)
            return serializer.data
        recipes = Recipe.objects.filter(author=obj.subscription_id)
        serializer = RecipeMinifiedSerializer(recipes, many=True)
        return serializer.data

    def get_is_subscribed(self, obj):
        """Метод, подписанн ли пользователь."""
        if self.context['request'].method == 'POST':
            return Subscription.objects.filter(subscription=obj.id).exists()
        return Subscription.objects.filter(
            subscription=obj.subscription_id
        ).exists()

    def get_username(self, obj):
        """Метод получения юзернейма подписчика."""
        if self.context['request'].method == 'POST':
            return obj.username
        return obj.subscription.username

    def get_id(self, obj):
        """Метод получения id подписчика."""
        if self.context['request'].method == 'POST':
            return obj.id
        return obj.subscription.id

    def get_first_name(self, obj):
        """Метод получения first_name подписчика."""
        if self.context['request'].method == 'POST':
            return obj.first_name
        return obj.subscription.first_name

    def get_last_name(self, obj):
        """Метод получения last_name подписчика."""
        if self.context['request'].method == 'POST':
            return obj.last_name
        return obj.subscription.last_name

    def get_email(self, obj):
        """Метод получения email подписчика."""
        if self.context['request'].method == 'POST':
            return obj.email
        return obj.subscription.email

    def get_avatar(self, obj):
        """Метод получения аватора подписчика."""
        request = self.context.get('request')
        if self.context['request'].method == 'POST':
            if not obj.avatar:
                return None
            return request.build_absolute_uri(obj.avatar.url)

        if obj.subscription.avatar:
            return request.build_absolute_uri(obj.subscription.avatar.url)
        return None
