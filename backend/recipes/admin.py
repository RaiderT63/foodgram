from django.contrib import admin
from django.db import models

from .models import (
    Tag,
    Ingredient,
    Recipe,
    RecipeIngredient,
    FavoriteRecipe,
    ShoppingItem
)


class RecipeIngredientInLine(admin.TabularInline):
    model = RecipeIngredient
    min_num = 1


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = (
        'name',
        'slug',
    )
    search_fields = (
        'name',
    )


@admin.register(Ingredient)
class IngredientAdmin(admin.ModelAdmin):
    list_display = (
        'name',
        'measurement_unit',
    )
    search_fields = (
        'name',
    )


@admin.register(Recipe)
class RecipeAdmin(admin.ModelAdmin):
    list_display = (
        'name',
        'author',
        'favorite_count',
    )
    search_fields = (
        'name',
    )
    list_filter = (
        'tags',
    )
    filter_horizontal = (
        'tags',
    )
    inlines = (
        RecipeIngredientInLine,
    )

    def get_queryset(self, request):
        return (
            super()
            .get_queryset(request)
            .select_related('author')
            .prefetch_related(
                'tags', 'ingredients', 'recipeingredients__ingredient'
            )
            .annotate(favorite_count=models.Count('favorite_recipes'))
        )


@admin.register(FavoriteRecipe)
class FavoriteRecipeAdmin(admin.ModelAdmin):
    list_display = (
        'user',
        'recipe',
    )
    search_fields = (
        'user__username',
        'recipe__name',
    )


@admin.register(ShoppingItem)
class ShoppingItemAdmin(admin.ModelAdmin):
    list_display = (
        'user',
        'recipe',
    )
    search_fields = (
        'user__username',
        'recipe__name',
    )
