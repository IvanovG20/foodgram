from django.urls import path, include

from rest_framework.routers import SimpleRouter

from api.views import (UserViewset, TagViewSet,
                       IngredientViewSet, RecipeViewSet)

router = SimpleRouter()
router.register('users', UserViewset, basename='users')
router.register('tags', TagViewSet, basename='tags')
router.register('ingredients', IngredientViewSet, basename='ingredients')
router.register('recipes', RecipeViewSet, basename='recipes')


urlpatterns = [
    path('auth/', include('djoser.urls.authtoken')),
    path('', include(router.urls)),
]
