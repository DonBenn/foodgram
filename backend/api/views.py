from django.db.models import F
from django.contrib.auth import get_user_model
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from djoser.conf import settings
from djoser.views import UserViewSet
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from api.filters import IngredientFilter, RecipeFilter
from api.paginators import LimitNumberPaginator, LimitSubscriptionsPaginator
from api.permissions import IsAuthorOrAdminOnly
from api.serializers import (AvatarSeializer, FavoriteCreateSerializer,
                             IngredientSerializer, UserListSerializer,
                             RecipeCreateSerializer, RecipeSerializer,
                             ShoppingCartSerializer, TagSerializer,
                             SubscriptionCreateSerializer,
                             SubscriptionSerializer)
from api.utils import generate_short_url
from foodgram.models import Ingredient, Recipe, Tag
from short_url.models import ShortLink

Profile = get_user_model()


class ProfileViewSet(UserViewSet):
    """Настройки вьюсета модели Пользователя."""

    queryset = Profile.objects.all()
    serializer_class = UserListSerializer
    pagination_class = LimitNumberPaginator

    def get_permissions(self):
        """Метод получает разрешения для текущего пользователя."""
        if self.action == 'retrieve':
            self.permission_classes = settings.PERMISSIONS.user
        elif self.action == 'list':
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
        serializer = UserListSerializer(
            request.user, context={'request': request}
        )
        return Response(serializer.data, status=status.HTTP_200_OK)

    @action(
        methods=['PUT', 'DELETE'],
        detail=False,
        permission_classes=(IsAuthorOrAdminOnly,),
        url_path='me/avatar'
    )
    def add_delete_avatar(self, request):
        """Метод создания удаления аватора пользователя."""
        if self.request.method == 'PUT':
            serializer = AvatarSeializer(request.user, data=request.data)
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        request.user.avatar.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(
        methods=['GET'],
        detail=False,
        permission_classes=(IsAuthorOrAdminOnly,),
        url_path='subscriptions',
    )
    def get_subscriptions(self, request):
        """Метод получения подписок пользователя."""

        users_we_follow = Profile.objects.filter(
            subscriber__subscription=request.user
        )
        limit_param = request.query_params.get('recipes_limit')
        paginator = LimitSubscriptionsPaginator()
        paginated_users_we_follow = paginator.paginate_queryset(
            users_we_follow,
            request
        )
        serializer = SubscriptionSerializer(
            paginated_users_we_follow,
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
        subscription = get_object_or_404(Profile, id=id)
        if request.method == 'POST':
            serializer = SubscriptionCreateSerializer(data={
                'user': request.user.id,
                'subscription': subscription.id},
                context={'request': request}
            )
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        if not request.user.subscriber.filter(
            subscription=subscription
        ).exists():
            return Response(
                'Не существует такой подписки',
                status=status.HTTP_400_BAD_REQUEST
            )
        unsubscribe = request.user.subscriber.filter(subscription=subscription)
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
        if self.action == 'create' or self.action == 'partial_update':
            return RecipeCreateSerializer
        return RecipeSerializer

    def get_permissions(self):
        """Метод получает разрешения для текущего пользователя."""
        if self.action == 'create':
            self.permission_classes = [IsAuthenticated]
        if self.action == 'partial_update' or (
            self.action == 'delete'
        ):
            self.permission_classes = [IsAuthorOrAdminOnly]
        return super().get_permissions()

    @action(
        methods=['GET'],
        detail=True,
        url_path='get-link'
    )
    def get_link(self, request, pk):
        """Метод получения короткой ссылки рецепта."""
        get_object_or_404(Recipe, id=pk)
        full_url = request.build_absolute_uri()
        long_url = full_url.replace('api/', '').replace('get-link/', '')
        short_url = generate_short_url()
        url, created = ShortLink.objects.get_or_create(long_url=long_url)

        if not created:
            short_prefix = '/s/' + url.short_url
            new_url = request.build_absolute_uri(short_prefix)
            return Response({'short-link': new_url}, status=status.HTTP_200_OK)

        url.short_url = short_url
        url.save()
        short_prefix = '/s/' + url.short_url
        new_url = request.build_absolute_uri(short_prefix)
        return Response({'short-link': new_url}, status=status.HTTP_200_OK)

    @action(
        methods=['POST', 'DELETE'],
        detail=True,
        permission_classes=(IsAuthorOrAdminOnly,),
        url_path='favorite'
    )
    def add_delete_favorite(self, request, pk):
        """Метод добавления удаления рецепта в избранное."""
        recipe = get_object_or_404(Recipe, id=pk)
        if request.method == 'POST':
            serializer = FavoriteCreateSerializer(data={
                'user': request.user,
                'recipe': recipe.id,
            })
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        if not request.user.favorite.filter(recipe=recipe).exists():
            return Response(
                'Нет такого рецепта в избранном',
                status=status.HTTP_400_BAD_REQUEST
            )
        favorite = request.user.favorite.filter(recipe=recipe)
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
        recipe = get_object_or_404(Recipe, id=pk)
        if request.method == 'POST':
            serializer = ShoppingCartSerializer(data={
                'user': request.user,
                'recipe': recipe.id,
            })
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response(
                serializer.data, status=status.HTTP_201_CREATED
            )
        if not request.user.shopping_cart.filter(recipe=recipe).exists():
            return Response(
                'Нет такого рецепта в корзине',
                status=status.HTTP_400_BAD_REQUEST
            )
        recipe_in_shopping_cart = request.user.shopping_cart.filter(
            recipe=recipe
        )
        recipe_in_shopping_cart.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(
        methods=['GET'],
        detail=False,
        permission_classes=(IsAuthorOrAdminOnly,),
        url_path='download_shopping_cart'
    )
    def download_shopping_cart(self, request):
        """Метод позволяющий скачать список покупок."""
        ingredients = Ingredient.objects.filter(
            recipes__shopping_cart__user=request.user).annotate(
            amount=F('ingredient_recipe__amount')
        )
        all_list = {}
        for ingredient in ingredients:
            if (
                f'{ingredient.name} ({ingredient.measurement_unit})'
            ) in all_list:
                all_list[
                    f'{ingredient.name} ({ingredient.measurement_unit})'
                ] += int(f'{ingredient.amount}')
            else:
                all_list[
                    f'{ingredient.name} ({ingredient.measurement_unit})'
                ] = int(f'{ingredient.amount}')
        response = HttpResponse(content_type='text/plain')
        response['Content-Disposition'] = 'attachment; filename="Покупки.txt"'
        for key, value in all_list.items():
            response.write(f'{key.capitalize()} - {value}\n')
        return response
