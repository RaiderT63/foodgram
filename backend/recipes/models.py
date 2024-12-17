from django.contrib.auth import get_user_model
from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator

from core.constants import (
    MIN_VALUE_LIMITS,
    MAX_VALUE_LIMITS,
)

User = get_user_model()


class Category(models.Model):
    title = models.CharField(
        'Название категории',
        max_length=50,
        unique=True
    )
    slug = models.SlugField(
        'Уникальный идентификатор',
        max_length=50,
        unique=True
    )

    class Meta:
        verbose_name = 'Категория'
        verbose_name_plural = 'Категории'
        db_table = 'category'

    def __str__(self):
        return self.title


class Ingredient(models.Model):
    name = models.CharField(
        'Название ингредиента',
        max_length=200,
        unique=True
    )
    unit_of_measurement = models.CharField(
        'Единица измерения',
        max_length=100
    )

    class Meta:
        verbose_name = 'Ингредиент'
        verbose_name_plural = 'Ингредиенты'
        db_table = 'ingredient'

    def __str__(self):
        return f'{self.name} ({self.unit_of_measurement})'


class Recipe(models.Model):
    creator = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='recipes_created',
        verbose_name='Создатель'
    )
    title = models.CharField(
        'Название рецепта',
        max_length=255
    )
    image = models.ImageField(
        'Фотография рецепта',
        upload_to='recipe_photos/'
    )
    description = models.TextField(
        'Описание рецепта'
    )
    ingredients = models.ManyToManyField(
        Ingredient,
        through='RecipeIngredient',
        related_name='used_in_recipes',
        verbose_name='Ингредиенты'
    )
    categories = models.ManyToManyField(
        Category,
        related_name='recipes_with_category',
        verbose_name='Категории'
    )
    cook_time = models.PositiveSmallIntegerField(
        'Время приготовления (минуты)',
        validators=[
            MinValueValidator(MIN_VALUE_LIMITS),
            MaxValueValidator(MAX_VALUE_LIMITS),
        ]
    )

    class Meta:
        verbose_name = 'Рецепт'
        verbose_name_plural = 'Рецепты'
        ordering = ['-id']
        db_table = 'recipe'

    def __str__(self):
        return self.title


class RecipeIngredient(models.Model):
    ingredient = models.ForeignKey(
        Ingredient,
        on_delete=models.CASCADE,
        verbose_name='Ингредиент'
    )
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        verbose_name='Рецепт'
    )
    quantity = models.PositiveSmallIntegerField(
        'Количество ингредиента',
        validators=[
            MinValueValidator(MIN_VALUE_LIMITS),
            MaxValueValidator(MAX_VALUE_LIMITS),
        ]
    )

    class Meta:
        verbose_name = 'Ингредиент в рецепте'
        verbose_name_plural = 'Ингредиенты в рецепте'
        db_table = 'recipe_ingredient'

    def __str__(self):
        return (
            f'{self.recipe.title}: {self.ingredient.name} — '
            f'{self.quantity} {self.ingredient.unit_of_measurement}'
        )


class FavoriteRecipe(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='favorite_recipes',
        verbose_name='Пользователь'
    )
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name='favorited_by_users',
        verbose_name='Избранный рецепт'
    )

    class Meta:
        verbose_name = 'Избранный рецепт'
        verbose_name_plural = 'Избранные рецепты'
        unique_together = ('user', 'recipe')
        db_table = 'favorite_recipe'

    def __str__(self):
        return (
            f'{self.user.username} добавил "{self.recipe.title}" '
            'в избранное'
        )


class ShoppingItem(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='shopping_items',
        verbose_name='Пользователь'
    )
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name='in_users_shopping_list',
        verbose_name='Рецепт для покупки'
    )

    class Meta:
        verbose_name = 'Элемент списка покупок'
        verbose_name_plural = 'Список покупок'
        unique_together = ('user', 'recipe')
        db_table = 'shopping_item'

    def __str__(self):
        return (
            f'{self.user.username} добавил "{self.recipe.title}" '
            'в список покупок'
        )
