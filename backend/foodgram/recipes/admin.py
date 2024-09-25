from django.contrib import admin
from recipes.models import (Favorite, Ingredient, Recipe, RecipeIngredient,
                            RecipeTag, ShoppingCart, Tag)


class RecipeIngredientInLine(admin.TabularInline):
    model = RecipeIngredient
    extra = 1


class RecipeTagInLine(admin.TabularInline):
    model = RecipeTag
    extra = 1


class RecipeAdmin(admin.ModelAdmin):
    inlines = (RecipeIngredientInLine, RecipeTagInLine,)
    list_display = ('name', 'author', 'is_favorited',
                    'ingredients', 'tags')
    list_filter = ('author', 'name', 'tags__name',)
    search_fields = (
        'name', 'author', 'tags__name',
        'ingredients__name',
    )

    @admin.display(description='Избранное')
    def is_favorited(self, obj):
        return obj.favorite.count()

    @admin.display(description='Теги рецепта')
    def tags(self, obj):
        return [str(tag.name) for tag in obj.recipe_tag.all()]

    @admin.display(description='Ингредиенты рецепта')
    def ingredients(self, obj):
        return [str(ingredient.name) for ingredient in obj.ingredient.all()]


class IngredientAdmin(admin.ModelAdmin):
    list_display = ('name', 'measurement_unit',)
    list_filter = ('name',)
    search_fields = ('name',)


class TagAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug',)
    list_filter = ('name',)
    search_fields = ('name', 'slug',)


admin.site.register(Tag, TagAdmin)
admin.site.register(Recipe, RecipeAdmin)
admin.site.register(RecipeTag)
admin.site.register(RecipeIngredient)
admin.site.register(Favorite)
admin.site.register(ShoppingCart)
admin.site.register(Ingredient, IngredientAdmin)
