from django.contrib import admin

from recipes.models import (Tag, Recipe, RecipeIngredient,
                            RecipeTag, Favorite, ShoppingCart,
                            Ingredient)


class RecipeAdmin(admin.ModelAdmin):
    list_display = ('name', 'author')
    list_filter = ('author', 'name', 'tags__name')


class IngredientAdmin(admin.ModelAdmin):
    list_display = ('name', 'measurement_unit')
    list_filter = ('name',)


admin.site.register(Tag)
admin.site.register(Recipe, RecipeAdmin)
admin.site.register(RecipeTag)
admin.site.register(RecipeIngredient)
admin.site.register(Favorite)
admin.site.register(ShoppingCart)
admin.site.register(Ingredient, IngredientAdmin)
