from django.urls import include, path
from rest_framework.routers import SimpleRouter

from api.views import IngredientViewSet, RecipeViewSet, TagViewSet, UserViewset

app_name = 'api'

router = SimpleRouter()
router.register('users', UserViewset, basename='users')
router.register('tags', TagViewSet, basename='tags')
router.register('ingredients', IngredientViewSet, basename='ingredients')
router.register('recipes', RecipeViewSet, basename='recipes')


urlpatterns = [
    path('auth/', include('djoser.urls.authtoken')),
    path('', include(router.urls)),
]
