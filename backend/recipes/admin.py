from django.contrib import admin

from .models import (
    Tag,
    Ingredient,
    Recipe,
    RecipeIngredient,
    FavoriteRecipe,
    ShoppingItem
)


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
        'get_favorite_count',
    )
    search_fields = (
        'name',
        'creator__username',
    )
    list_filter = (
        'tags',
    )
    filter_horizontal = (
        'tags',
    )

    def get_favorite_count(self, obj):
        return obj.favorited_by_users.count()
    get_favorite_count.short_description = 'Добавлений в избранное'


@admin.register(RecipeIngredient)
class RecipeIngredientAdmin(admin.ModelAdmin):
    list_display = (
        'recipe',
        'amount',
        'ingredient',
    )
    search_fields = (
        'ingredient__name',
    )
    list_filter = (
        'recipe',
        'ingredient',
    )


@admin.register(FavoriteRecipe)
class FavoriteRecipeAdmin(admin.ModelAdmin):
    list_display = (
        'user',
        'recipe',
    )
    search_fields = (
        'user__username',
        'recipe__title',
    )


@admin.register(ShoppingItem)
class ShoppingItemAdmin(admin.ModelAdmin):
    list_display = (
        'user',
        'recipe',
    )
    search_fields = (
        'user__username',
        'recipe__title',
    )
