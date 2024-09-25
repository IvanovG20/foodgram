from api.views import (IngredientListView, RecipeViewSet,
                       TagListView, UserViewset)
from django.urls import include, path
from rest_framework.routers import SimpleRouter

app_name = 'api'

router_v1 = SimpleRouter()
router_v1.register('users', UserViewset, basename='users')
router_v1.register('recipes', RecipeViewSet, basename='recipes')


urlpatterns = [
    path('auth/', include('djoser.urls.authtoken')),
    path('tags/', TagListView.as_view(), name='tags'),
    path(
        'ingredients/',
        IngredientListView.as_view(),
        name='ingredients'),
    path('', include(router_v1.urls)),
]
