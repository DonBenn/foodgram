from django.contrib.auth.models import AbstractUser
from django.core.validators import (FileExtensionValidator, MaxValueValidator,
                                    MinValueValidator)
from django.db import models
from django.db.models import Q

from foodgram.constants import (MAX_COOKING_TIME_SCORE, MAX_EMAIL_LENGTH,
                                MAX_FIRST_NAME_LENGTH, MAX_INGREDIENT_LENGTH,
                                MAX_LAST_NAME_LENGTH, MAX_PASSWORD_LENGTH,
                                MAX_RECIPE_LENGTH, MAX_TAG_LENGTH,
                                MAX_USERNAME_LENGTH, MIN_COOKING_TIME_SCORE,
                                MAX_AMOUNT_VALUE, MIN_AMOUNT_VALUE)
from foodgram.validators import validate_username


class Profile(AbstractUser):
    """Настройки модели Пользователя."""

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ('username', 'first_name', 'last_name')

    username = models.CharField(
        max_length=MAX_USERNAME_LENGTH,
        verbose_name='Юзернейм пользователя',
        unique=True,
        validators=(validate_username,),
    )
    first_name = models.CharField(
        max_length=MAX_FIRST_NAME_LENGTH,
        verbose_name='Имя',
    )
    last_name = models.CharField(
        max_length=MAX_LAST_NAME_LENGTH,
        verbose_name='Фамилия пользователя',
    )
    email = models.EmailField(
        'Почта',
        max_length=MAX_EMAIL_LENGTH,
        unique=True
    )
    password = models.CharField(
        max_length=MAX_PASSWORD_LENGTH,
        verbose_name='Пароль',
    )
    avatar = models.ImageField(
        upload_to='users/',
        blank=True,
        null=True,
        validators=[FileExtensionValidator(allowed_extensions=['jpg', 'png'])]
    )

    class Meta:
        """Метаданные модели группы."""

        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'
        ordering = ['username']
        constraints = [
            models.UniqueConstraint(
                fields=('username', 'email'), name='username_email_constraint'
            ),
        ]

    def __str__(self):
        """Возвращает строковое представление объекта."""
        return self.username


class Tag(models.Model):
    """Настройки модели Тэгов."""

    name = models.CharField(
        max_length=MAX_TAG_LENGTH,
        unique=True,
        verbose_name='Название'
    )
    slug = models.SlugField(
        max_length=MAX_TAG_LENGTH,
        unique=True,
        verbose_name='Slug'
    )

    class Meta:
        """Метаданные модели группы."""

        ordering = ['name']
        verbose_name = 'Тег'
        verbose_name_plural = 'Теги'
        constraints = [
            models.UniqueConstraint(
                fields=('name', 'slug'),
                name='name_slug_constraint'
            ),
        ]

    def __str__(self):
        """Возвращает строковое представление объекта."""
        return self.name


class Ingredient(models.Model):
    """Настройки модели Ингредиентов."""

    name = models.CharField(
        max_length=MAX_INGREDIENT_LENGTH,
        verbose_name='Название',
        db_index=True
    )
    measurement_unit = models.CharField(
        max_length=MAX_INGREDIENT_LENGTH,
        verbose_name='Единица измерения'
    )

    class Meta:
        """Метаданные модели группы."""

        ordering = ['name']
        verbose_name = 'Ингредиент'
        verbose_name_plural = 'Ингредиенты'
        constraints = [
            models.UniqueConstraint(
                fields=('name', 'measurement_unit'),
                name='name_measurement_unit_constraint'
            ),
        ]

    def __str__(self):
        """Возвращает строковое представление объекта."""
        return self.name


class Recipe(models.Model):
    """Настройки модели Рецептов."""

    author = models.ForeignKey(
        Profile, on_delete=models.CASCADE, related_name='recipes'
    )
    name = models.CharField(max_length=MAX_RECIPE_LENGTH)
    ingredients = models.ManyToManyField(
        Ingredient, through='IngredientRecipe',
        related_name='recipes',
    )
    tags = models.ManyToManyField(
        Tag, through='TagRecipe',
        related_name='recipes',
    )
    image = models.ImageField(
        upload_to='recipes/images/',
        validators=[FileExtensionValidator(allowed_extensions=['jpg', 'png'])]
    )
    text = models.TextField()
    cooking_time = models.PositiveSmallIntegerField(
        validators=[
            MinValueValidator(MIN_COOKING_TIME_SCORE),
            MaxValueValidator(MAX_COOKING_TIME_SCORE),
        ],
    )
    created = models.DateTimeField(
        verbose_name='Дата создания',
        auto_now_add=True,
    )

    class Meta:
        """Метаданные модели группы."""

        ordering = ['-created']
        verbose_name = 'Рецепт'
        verbose_name_plural = 'Рецепты'

    def __str__(self):
        """Возвращает строковое представление объекта."""
        return self.name

    def get_favorite_count(self):
        """Функция подсчёта колличества избанного у рецепта."""
        return self.favorite.count()


class TagRecipe(models.Model):
    """Настройки модели Тэгов рецепта."""

    tag = models.ForeignKey(
        Tag, on_delete=models.CASCADE,
        related_name='tag_recipe'
    )
    recipe = models.ForeignKey(
        Recipe, on_delete=models.CASCADE,
        related_name='tag_recipe'
    )

    class Meta:
        """Метаданные модели Избранное."""

        ordering = ('recipe',)
        verbose_name = 'Тег рецепта'
        verbose_name_plural = 'Тэги рецепта'

    def __str__(self):
        """Возвращает строковое представление объекта."""
        return f'{self.tag} {self.recipe}'


class IngredientRecipe(models.Model):
    """Настройки модели Ингредиентов Рецепта."""

    ingredient = models.ForeignKey(
        Ingredient, on_delete=models.CASCADE,
        related_name='ingredient_recipe'
    )
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name='ingredient_recipe'
    )
    amount = models.PositiveSmallIntegerField(
        validators=[
            MinValueValidator(MIN_AMOUNT_VALUE),
            MaxValueValidator(MAX_AMOUNT_VALUE),
        ],
    )

    class Meta:
        """Метаданные модели Избранное."""

        ordering = ('recipe',)
        verbose_name = 'Ингредиент рецепта'
        verbose_name_plural = 'Ингредиенты рецепта'

    def __str__(self):
        """Возвращает строковое представление объекта."""
        return f'{self.ingredient} {self.recipe}'


class Favorite(models.Model):
    """Настройки модели Избранное."""

    user = models.ForeignKey(
        Profile, on_delete=models.CASCADE, related_name='favorite'
    )
    recipe = models.ForeignKey(
        Recipe, on_delete=models.CASCADE, related_name='favorite'
    )

    class Meta:
        """Метаданные модели Избранное."""

        ordering = ('recipe',)
        verbose_name = 'Избранный'
        verbose_name_plural = 'Избранное'
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'recipe'],
                name='unique_user_recipe'
            )
        ]

    def __str__(self):
        """Возвращает строковое представление объекта."""
        return f'{self.user} {self.recipe}'


class ShoppingCart(models.Model):
    """Настройки модели Список покупок."""

    user = models.ForeignKey(
        Profile, on_delete=models.CASCADE, related_name='shopping_cart'
    )
    recipe = models.ForeignKey(
        Recipe, on_delete=models.CASCADE, related_name='shopping_cart'
    )

    class Meta:
        """Метаданные модели Список покупок."""

        ordering = ('recipe',)
        verbose_name = 'Список покупок'
        verbose_name_plural = 'Список покупок'
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'recipe'],
                name='unique_user_shopping_cart_recipe'
            )
        ]

    def __str__(self):
        """Возвращает строковое представление объекта."""
        return f'{self.user} {self.recipe}'


class Subscription(models.Model):
    """Настройки модели Подписок."""

    user = models.ForeignKey(
        Profile, on_delete=models.CASCADE, related_name='subscriber')
    subscription = models.ForeignKey(
        Profile, on_delete=models.CASCADE, related_name='subscription')

    class Meta:
        """Метаданные модели подписок."""

        ordering = ('subscription',)
        verbose_name = 'Подписчик'
        verbose_name_plural = 'Подписчики'
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'subscription'],
                name='unique_user_subscription',
            ),
            models.CheckConstraint(
                check=~Q(user=models.F('subscription')),
                name='not_self_subscription'
            )
        ]

    def __str__(self):
        """Возвращает строковое представление объекта."""
        return f'{self.user} {self.subscription}'
