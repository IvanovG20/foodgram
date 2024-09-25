import random
import string

from django.contrib.auth import get_user_model
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from recipes.constants import (INGREDIENT_CONST, MAX_LIMIT_VALUE,
                               MIN_LIMIT_VALUE, RECIPE_NAME_CONST,
                               SHORT_LINK_CONST, TAG_CONST)

User = get_user_model()


class Tag(models.Model):
    name = models.CharField(
        max_length=TAG_CONST,
        unique=True,
        verbose_name='Название тега'
    )
    slug = models.SlugField(
        max_length=TAG_CONST,
        unique=True,
        verbose_name='Уникальный слаг'
    )

    class Meta:
        verbose_name = 'тег'
        verbose_name_plural = 'Теги'

    def __str__(self):
        return self.name


class Ingredient(models.Model):
    name = models.CharField(
        max_length=INGREDIENT_CONST,
        unique=True,
        verbose_name='Название ингредиента'
    )
    measurement_unit = models.CharField(
        max_length=INGREDIENT_CONST,
        verbose_name='Единица измерения'
    )

    class Meta:
        verbose_name = 'ингредиент'
        verbose_name_plural = 'Ингредиенты'

    def __str__(self):
        return self.name


class Recipe(models.Model):
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name='Автор рецепта',
        related_name='recipes'
    )
    name = models.CharField(
        max_length=RECIPE_NAME_CONST,
        verbose_name='Название рецепта'
    )
    image = models.ImageField(
        upload_to='recipes/',
        verbose_name='Картинка рецепта',
        blank=False
    )
    text = models.TextField(
        verbose_name='Описание рецепта'
    )
    cooking_time = models.PositiveSmallIntegerField(
        verbose_name='Время готовки в минутах',
        validators=[
            MinValueValidator(limit_value=MIN_LIMIT_VALUE),
            MaxValueValidator(limit_value=MAX_LIMIT_VALUE)
        ]
    )
    tags = models.ManyToManyField(
        Tag,
        through='RecipeTag',
        related_name='recipes',
        verbose_name='Теги рецепта'
    )
    ingredients = models.ManyToManyField(
        Ingredient,
        through='RecipeIngredient',
        related_name='recipes',
        verbose_name='Ингредиенты рецепта'
    )

    short_link = models.CharField(
        max_length=SHORT_LINK_CONST,
        blank=True,
        unique=True,
        null=True,
        verbose_name='Короткая ссылка',
    )

    class Meta:
        verbose_name = 'рецепт'
        verbose_name_plural = 'Рецепты'

    def generate_short_link(self):
        while True:
            short_link = ''.join(
                random.choices(
                    string.ascii_letters + string.digits,
                    k=SHORT_LINK_CONST
                )
            )
            if not Recipe.objects.filter(short_link=short_link).exists():
                return short_link

    def save(self, *args, **kwargs):
        if not self.short_link:
            self.short_link = self.generate_short_link()
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


class RecipeTag(models.Model):
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name='recipe_tag',
        verbose_name='рецепт'
    )
    tag = models.ForeignKey(
        Tag,
        on_delete=models.CASCADE,
        verbose_name='тег'
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=('recipe', 'tag'),
                name='recipetag_unique'
            )
        ]
        verbose_name = 'тег рецепта'
        verbose_name_plural = 'Теги рецепта'


class RecipeIngredient(models.Model):
    recipe = models.ForeignKey(
        Recipe, on_delete=models.CASCADE,
        related_name='ingredient',
        verbose_name='рецепт'
    )
    ingredient = models.ForeignKey(
        Ingredient,
        on_delete=models.CASCADE,
        verbose_name='ингредиент'
    )
    amount = models.PositiveSmallIntegerField(
        verbose_name='Колличество ингредиента',
        validators=[
            MinValueValidator(limit_value=MIN_LIMIT_VALUE),
            MaxValueValidator(limit_value=MAX_LIMIT_VALUE)
        ]
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=('recipe', 'ingredient'),
                name='recipeingredient_unique'
            )
        ]
        verbose_name = 'ингредиент рецепта'
        verbose_name_plural = 'Ингредиенты рецепта'


class Favorite(models.Model):
    recipe = models.ForeignKey(
        Recipe, on_delete=models.CASCADE,
        related_name='favorite'
    )
    user = models.ForeignKey(
        User, on_delete=models.CASCADE,
        related_name='favorite'
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=('recipe', 'user'),
                name='favorite_unique'
            )
        ]

        verbose_name = 'избранное'
        verbose_name_plural = 'Избранные'


class ShoppingCart(models.Model):
    recipe = models.ForeignKey(
        Recipe, on_delete=models.CASCADE,
        related_name='shopping_cart'
    )
    user = models.ForeignKey(
        User, on_delete=models.CASCADE,
        related_name='shopping_cart'
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=('recipe', 'user'),
                name='shopping_cart_unique'
            )
        ]
        verbose_name = 'корзина покупок'
        verbose_name = 'Корзины покупок'
