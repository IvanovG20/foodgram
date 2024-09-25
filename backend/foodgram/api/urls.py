from django.urls import include, path
from rest_framework.routers import SimpleRouter

from api.views import IngredientViewset, RecipeViewSet, TagViewset, UserViewset

app_name = 'api'

router_v1 = SimpleRouter()
router_v1.register('users', UserViewset, basename='users')
router_v1.register('tags', TagViewset, basename='tags')
router_v1.register('ingredients', IngredientViewset, basename='ingredients')
router_v1.register('recipes', RecipeViewSet, basename='recipes')


urlpatterns = [
    path('auth/', include('djoser.urls.authtoken')),
    path('', include(router_v1.urls)),
]
