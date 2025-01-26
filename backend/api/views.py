import random
import string

from api.filters import IngredientFilter, RecipeFilter
from api.paginators import LimitNumberPaginator, LimitSubscriptionsPaginator
from api.permissions import IsAuthorOrAdminOnly
from api.serializers import (AvatarSeializer, FavoriteCreateSerializer,
                             IgredientAmountSerializer, IngredientSerializer,
                             RecipeCreateSerializer, RecipeMinifiedSerializer,
                             RecipeSerializer, ShoppingCartSerializer,
                             SubscriptionCreateSerializer,
                             SubscriptionSerializer, TagSerializer,
                             UserListSerializer)
from django.contrib.auth import get_user_model
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from djoser.conf import settings
from djoser.views import UserViewSet
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from short_url.models import ShortLink

from foodgram.constants import MAX_SHORT_URL_LENGTH
from foodgram.models import Favorite, Ingredient, Recipe, Subscription, Tag

CustomUser = get_user_model()


def generate_short_url():
    """Функция генерации короткой ссылки рецепта."""
    letters_digits = string.digits + string.ascii_letters
    while True:
        short_url = ''.join(
            random.choice(letters_digits) for element in range(
                MAX_SHORT_URL_LENGTH
            )
        )
        if not ShortLink.objects.filter(short_url=short_url).exists():
            return short_url


class CustomUserViewSet(UserViewSet):
    """Настройки вьюсета модели Пользователя."""

    queryset = CustomUser.objects.all()
    serializer_class = UserListSerializer
    pagination_class = LimitNumberPaginator

    def get_permissions(self):
        """Метод получает разрешения для текущего пользователя."""
        if self.action == "retrieve":
            self.permission_classes = settings.PERMISSIONS.user
        elif self.action == "list":
            self.permission_classes = settings.PERMISSIONS.user_list

        return super().get_permissions()

    @action(
        methods=['GET'],
        detail=False,
        permission_classes=(IsAuthorOrAdminOnly,),
        url_path='me'
    )
    def get_current_user_info(self, request):
        """Метод получает информацию о текущем пользователе."""
        user = request.user
        serializer = UserListSerializer(user, context={'request': request})
        return Response(serializer.data, status=status.HTTP_200_OK)

    @action(
        methods=['PUT', 'DELETE'],
        detail=False,
        permission_classes=(IsAuthorOrAdminOnly,),
        url_path='me/avatar'
    )
    def add_delete_avatar(self, request):
        """Метод создания удаления аватора пользователя."""
        user = CustomUser.objects.get(id=request.user.id)
        data = request.data
        if self.request.method == 'PUT':
            serializer = AvatarSeializer(user, data=data)
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        elif self.request.method == 'DELETE':
            user.avatar.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)

    @action(
        methods=['GET'],
        detail=False,
        permission_classes=(IsAuthorOrAdminOnly,),
        url_path='subscriptions',
    )
    def get_subscriptions(self, request):
        """Метод получения подписок пользователя."""
        user = request.user
        subscription = user.subscriber.all()
        limit_param = request.query_params.get('recipes_limit')
        paginator = LimitSubscriptionsPaginator()
        paginated_subscriptions = paginator.paginate_queryset(
            subscription,
            request
        )
        serializer = SubscriptionSerializer(
            paginated_subscriptions,
            many=True,
            context={'request': request, 'limit_param': limit_param}
        )
        paginated_data = paginator.get_paginated_response(serializer.data)
        return paginated_data

    @action(
        methods=['POST', 'DELETE'],
        detail=True,
        permission_classes=(IsAuthorOrAdminOnly,),
        url_path='subscribe'
    )
    def set_subscription(self, request, id):
        """Метод создания удаления подписок пользователя."""
        user = self.request.user
        subscription = get_object_or_404(CustomUser, id=id)
        if request.method == 'POST':
            serializer = SubscriptionCreateSerializer(data={
                'user': user.id,
                'subscription': subscription.id},
                context={'request': request}
            )
            serializer.is_valid(raise_exception=True)
            serializer.save()
            subscribe = get_object_or_404(
                Subscription,
                user=user,
                subscription=subscription
            )
            serializer = SubscriptionSerializer(
                subscribe.subscription,
                context={'request': request}
            )
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        elif request.method == 'DELETE':
            if not user.subscriber.filter(subscription=subscription).exists():
                return Response(
                    'Не существует такой подписки',
                    status=status.HTTP_400_BAD_REQUEST
                )
            unsubscribe = user.subscriber.filter(subscription=subscription)
            unsubscribe.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)


class TagViewSet(viewsets.ModelViewSet):
    """Настройки вьюсета модели Тэгов."""

    queryset = Tag.objects.all()
    http_method_names = ['get']
    serializer_class = TagSerializer
    pagination_class = None


class IngredientViewSet(viewsets.ModelViewSet):
    """Настройки вьюсета модели Ингредиентов."""

    queryset = Ingredient.objects.all()
    http_method_names = ['get']
    serializer_class = IngredientSerializer
    filter_backends = (IngredientFilter,)
    search_fields = ('^name',)
    pagination_class = None


class RecipeViewSet(viewsets.ModelViewSet):
    """Настройки вьюсета модели Рецепта."""

    queryset = Recipe.objects.all()
    serializer_class = RecipeSerializer
    http_method_names = ['post', 'get', 'delete', 'patch']
    filter_backends = (DjangoFilterBackend,)
    filterset_class = RecipeFilter
    pagination_class = LimitNumberPaginator

    def get_serializer_class(self):
        """Метод выбора сериалайзера для рецепта."""
        if self.action == 'create':
            return RecipeCreateSerializer
        return RecipeSerializer

    def list(self, request, *args, **kwargs):
        """Метод получения списка рецептов."""
        queryset = self.filter_queryset(self.get_queryset())
        page = self.paginate_queryset(queryset)
        if page is not None:
            recipes_data = []
            for recipe in page:
                ingredients = recipe.ingredients.all()
                ingredient_serializer = IgredientAmountSerializer(
                    ingredients,
                    many=True,
                    context={'recipe': recipe}
                )
                recipe_serializer = RecipeSerializer(
                    recipe,
                    context={'request': request, 'recipe': recipe}
                )
                recipe_data = recipe_serializer.data
                recipe_data['ingredients'] = ingredient_serializer.data
                recipes_data.append(recipe_data)
            return self.get_paginated_response(recipes_data)

        recipes_data = []
        ingredients = recipe.ingredients.all()
        ingredient_serializer = IgredientAmountSerializer(
            ingredients,
            many=True,
            context={'recipe': recipe}
        )
        recipe_serializer = RecipeSerializer(
            recipe,
            context={'request': request, 'recipe': recipe}
        )
        recipe_data = recipe_serializer.data
        recipe_data['ingredients'] = ingredient_serializer.data
        return Response(recipes_data)

    def retrieve(self, request, pk):
        """Метод получения отдельного рецепта."""
        recipe = get_object_or_404(Recipe, id=pk)
        serializer = RecipeSerializer(recipe, context={
            'request': request,
            'recipe': recipe})
        return Response(serializer.data, status=status.HTTP_200_OK)

    def create(self, request):
        """Метод создания рецепта."""
        author = self.request.user
        if not author.is_authenticated:
            return Response(
                'Пользователь не авторизован',
                status=status.HTTP_401_UNAUTHORIZED
            )
        data = request.data
        if not data.get('ingredients'):
            return Response(
                'Выберите ингредиенты',
                status=status.HTTP_400_BAD_REQUEST
            )
        if not data.get('cooking_time'):
            return Response(
                'Введите время приготовления',
                status=status.HTTP_400_BAD_REQUEST
            )
        data_name = data.get('name')
        data_text = data.get('text')
        data_cooking_time = data.get('cooking_time')
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
        ingredients_count = len(data.get('ingredients'))
        serializer = RecipeCreateSerializer(data=data)
        serializer.is_valid(raise_exception=True)
        serializer.save(author=author)
        recipe = Recipe.objects.get(
            author=author,
            name=data_name,
            text=data_text,
            cooking_time=data_cooking_time
        )
        if not recipe:
            return Response(
                'Не удалось создать рецепт',
                status=status.HTTP_400_BAD_REQUEST
            )
        if ingredients_count == recipe.ingredients.count():
            serializer = RecipeSerializer(
                recipe,
                context={'request': request, 'recipe': recipe}
            )
            return Response(serializer.data, status=status.HTTP_201_CREATED)

    def update(self, request, pk, **kwargs):
        """Метод обновления рецепта."""
        author = self.request.user
        data = request.data
        if not author.is_authenticated:
            return Response(
                'Пользователь не авторизован',
                status=status.HTTP_401_UNAUTHORIZED
            )
        recipe = get_object_or_404(Recipe, id=pk)
        if not author.is_superuser and author != recipe.author:
            return Response(
                'Нельзя редактировать рецепт',
                status=status.HTTP_403_FORBIDDEN
            )
        if not data.get('tags'):
            return Response(
                'Нельзя редактировать рецепт без тегов',
                status=status.HTTP_400_BAD_REQUEST
            )
        if not data.get('ingredients'):
            return Response(
                'Нельзя редактировать рецепт без ингредиентов',
                status=status.HTTP_400_BAD_REQUEST
            )
        if len(data['ingredients']) < 2:
            return Response(
                'Введите больше одного ингредиента',
                status=status.HTTP_400_BAD_REQUEST
            )
        ingredients_count = len(data.get('ingredients'))
        serializer = RecipeCreateSerializer(
            recipe,
            data=request.data,
            partial=True
        )
        if serializer.is_valid():
            self.perform_update(serializer)
            recipe = Recipe.objects.get(id=pk)
            if not recipe:
                return Response(
                    'Не удалось обновить рецепт',
                    status=status.HTTP_400_BAD_REQUEST
                )
            if ingredients_count == recipe.ingredients.count():
                serializer = RecipeSerializer(
                    recipe,
                    context={'request': request, 'recipe': recipe}
                )
                return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def destroy(self, request, pk):
        """Метод удаления рецепта."""
        user = request.user
        recipe = self.get_object()
        if not user.is_authenticated:
            return Response(
                'Пользователь не авторизован',
                status=status.HTTP_401_UNAUTHORIZED
            )
        if not user.is_superuser and user != recipe.author:
            return Response(
                'Нельзя удалить рецепт',
                status=status.HTTP_403_FORBIDDEN
            )
        self.perform_destroy(recipe)
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(
        methods=['GET'],
        detail=True,
        url_path='get-link'
    )
    def get_link(self, request, pk):
        """Метод получения короткой ссылки рецепта."""
        recipe = get_object_or_404(Recipe, id=pk)
        long_url = request.build_absolute_uri(f'/recipes/{recipe.id}/')
        short_url = generate_short_url()
        url, created = ShortLink.objects.get_or_create(long_url=long_url)
        if not created:
            new_url = request.build_absolute_uri(f'/s/{url.short_url}')
            return Response({'short-link': new_url}, status=status.HTTP_200_OK)
        url.short_url = short_url
        url.save()
        new_url = request.build_absolute_uri(f'/s/{url.short_url}')
        return Response({'short-link': new_url}, status=status.HTTP_200_OK)

    @action(
        methods=['POST', 'DELETE'],
        detail=True,
        permission_classes=(IsAuthorOrAdminOnly,),
        url_path='favorite'
    )
    def add_delete_favorite(self, request, pk):
        """Метод добавления удаления рецепта в избранное."""
        user = self.request.user
        recipe = get_object_or_404(Recipe, id=pk)
        if request.method == 'POST':
            serializer = FavoriteCreateSerializer(data={
                'user': user,
                'recipe': recipe.id,
            })
            serializer.is_valid(raise_exception=True)
            serializer.save()
            favorite = get_object_or_404(Favorite, user=user, recipe=recipe)
            serializer = RecipeMinifiedSerializer(favorite.recipe)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        elif request.method == 'DELETE':
            if not user.favorite.filter(recipe=recipe).exists():
                return Response(
                    'Нет такого рецепта в избранном',
                    status=status.HTTP_400_BAD_REQUEST
                )
            # favorite = Favorite.objects.filter(user=user, recipe=recipe)
            favorite = user.favorite.filter(recipe=recipe)
            favorite.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)

    @action(
        methods=['POST', 'DELETE'],
        detail=True,
        permission_classes=(IsAuthorOrAdminOnly,),
        url_path='shopping_cart'
    )
    def add_delete_shopping_cart(self, request, pk):
        """Метод добавления удаления рецепта в список покупок."""
        user = self.request.user
        recipe = get_object_or_404(Recipe, id=pk)
        count = recipe.ingredients.count()
        if request.method == 'POST':
            serializer = ShoppingCartSerializer(data={
                'user': user,
                'recipe': recipe.id,
            })
            serializer.is_valid(raise_exception=True)
            serializer.save()
            recipes_in_shopping_cart = user.shopping_cart.filter(recipe=recipe)
            if not recipes_in_shopping_cart:
                return Response(
                    'Не удалось добавить рецепты в корзину',
                    status=status.HTTP_400_BAD_REQUEST
                )
            if count == recipes_in_shopping_cart.count():
                serializer = RecipeMinifiedSerializer(recipe)
                return Response(
                    serializer.data, status=status.HTTP_201_CREATED
                )
        elif request.method == 'DELETE':
            if not user.shopping_cart.filter(recipe=recipe).exists():
                return Response(
                    'Нет такого рецепта в корзине',
                    status=status.HTTP_400_BAD_REQUEST
                )
            recipes_in_shopping_cart = user.shopping_cart.filter(recipe=recipe)
            if count == recipes_in_shopping_cart.count():
                recipes_in_shopping_cart.delete()
                return Response(status=status.HTTP_204_NO_CONTENT)

    @action(
        methods=['GET'],
        detail=False,
        permission_classes=(IsAuthorOrAdminOnly,),
        url_path='download_shopping_cart'
    )
    def download_shopping_cart(self, request):
        """Метод позволяющий скачать список покупок."""
        user = self.request.user
        all_recipes = user.shopping_cart.all()
        all_list = {}
        for element in all_recipes:
            ingredient = Ingredient.objects.get(id=element.ingredient.id)
            if (
                f'{ingredient.name} ({ingredient.measurement_unit})'
            ) in all_list:
                all_list[
                    f'{ingredient.name} ({ingredient.measurement_unit})'
                ] += int(f'{element.amount}')
            else:
                all_list[
                    f'{ingredient.name} ({ingredient.measurement_unit})'
                ] = int(f'{element.amount}')
        response = HttpResponse(content_type='text/plain')
        response['Content-Disposition'] = 'attachment; filename="Покупки.txt"'
        for key, value in all_list.items():
            response.write(f'{key.capitalize()} - {value}\n')
        return response
