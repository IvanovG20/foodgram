from api.filters import RecipeFilter
from api.pagination import CustomPagination
from api.permissions import IsAuthorOrAuthenticatedOrRead
from api.serializers import (CreateRecipeSerializer, EasyRecipeSerializer,
                             IngredientSerializer, PasswordChangeSerializer,
                             RecipeSerializer, SubscriptionCreateSerializer,
                             SubscriptionShowSerializer, TagSerializer, User,
                             UserCreateSerializer, UserSerializer)
from django.db.models import Sum
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from recipes.models import (Favorite, Ingredient, Recipe, RecipeIngredient,
                            ShoppingCart, Tag)
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.filters import SearchFilter
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet
from users.models import Follow


class UserViewset(ModelViewSet):
    queryset = User.objects.all()
    pagination_class = CustomPagination

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return UserCreateSerializer
        return UserSerializer

    @action(
        detail=False, methods=['get'],
        permission_classes=[IsAuthenticated])
    def me(self, request):
        user = request.user
        serializer = UserSerializer(user)
        return Response(serializer.data)

    @action(
        detail=False, methods=['put',],
        permission_classes=[IsAuthenticated],
        url_path='me/avatar'
    )
    def avatar(self, request):
        user = request.user
        if 'avatar' not in request.data:
            return Response(status=status.HTTP_400_BAD_REQUEST)
        serializer = UserSerializer(
            user, data=request.data, partial=True
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        url = serializer.data.get('avatar')
        response = {'avatar': url}
        return Response(response, status=status.HTTP_200_OK)

    @avatar.mapping.delete
    def delete_avatar(self, request):
        user = request.user
        if not user.avatar:
            error_message = 'Аватар не найден'
            return Response(
                {'error': error_message},
                status=status.HTTP_400_BAD_REQUEST
            )
        user.avatar.delete()
        user.save()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=False, methods=['post'],
            permission_classes=[IsAuthenticated])
    def set_password(self, request):
        serializer = PasswordChangeSerializer(
            data=request.data, context={'request': request}
        )
        if serializer.is_valid():
            serializer.save()
            return Response(status=status.HTTP_204_NO_CONTENT)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(methods=['get'], detail=False,
            permission_classes=[IsAuthenticated])
    def subscriptions(self, request):
        user = request.user
        subs_list = User.objects.filter(
            following__in=user.follower.all()
        )
        serializer = SubscriptionShowSerializer(
            self.paginate_queryset(subs_list),
            many=True,
            context={'request': request}
        )
        return self.get_paginated_response(serializer.data)

    @action(detail=True, methods=['post',],
            permission_classes=[IsAuthenticated])
    def subscribe(self, request, pk):
        following = get_object_or_404(User, pk=pk)
        data = {
            'user': self.request.user.pk,
            'following': following.pk,
        }
        serializer = SubscriptionCreateSerializer(
            data=data,
            context={'request': request},
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(
            serializer.data,
            status=status.HTTP_201_CREATED
        )

    @subscribe.mapping.delete
    def delete_subscribe(self, request, pk):
        user = self.request.user
        following = get_object_or_404(User, pk=pk)
        deletes_count, _ = Follow.objects.filter(
            user=user, following=following
        ).delete()
        if deletes_count == 0:
            return Response(status=status.HTTP_400_BAD_REQUEST)
        return Response(status=status.HTTP_204_NO_CONTENT)


class TagViewset(viewsets.ReadOnlyModelViewSet):
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    pagination_class = None


class IngredientViewset(viewsets.ReadOnlyModelViewSet):
    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    pagination_class = None
    filter_backends = [SearchFilter, ]
    search_fields = ['^name']


class RecipeViewSet(ModelViewSet):
    queryset = Recipe.objects.order_by('-id')
    permission_classes = [IsAuthorOrAuthenticatedOrRead, ]
    pagination_class = CustomPagination
    http_method_names = [
        'get', 'post', 'patch', 'delete'
    ]
    filter_backends = (DjangoFilterBackend,)
    filterset_class = RecipeFilter

    def get_serializer_class(self):
        if self.request.method in ['POST', 'PATCH']:
            return CreateRecipeSerializer
        return RecipeSerializer

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)

    @action(detail=True, methods=['get'],
            url_path='get-link')
    def get_link(self, request, pk):
        recipe = get_object_or_404(Recipe, pk=pk)
        url = request.build_absolute_uri(f'/s/{recipe.short_link}')
        return Response(
            {'short-link': url},
            status=status.HTTP_200_OK
        )

    @action(detail=False, methods=['get'],
            url_path=r's/(?P<short_link>\w+)')
    def redirect_to_recipe(self, request, short_link):
        recipe = get_object_or_404(Recipe, short_link=short_link)
        return HttpResponseRedirect(
            request.build_absolute_uri('/recipes/' + str(recipe.pk) + '/')
        )

    def shop_fav_post_method(self, model, user, recipe):
        model.objects.create(user=user, recipe=recipe)
        serializer = EasyRecipeSerializer(recipe)
        return Response(
            serializer.data,
            status=status.HTTP_201_CREATED
        )

    def shop_fav_delete_method(self, model, user, recipe):
        model.objects.get(
            user=user, recipe=recipe
        ).delete()
        return Response(
            status=status.HTTP_204_NO_CONTENT
        )

    @action(detail=True, methods=['post',],
            permission_classes=[IsAuthenticated])
    def shopping_cart(self, request, pk):
        user = request.user
        recipe = get_object_or_404(Recipe, pk=pk)
        if ShoppingCart.objects.filter(
            user=user, recipe=recipe
        ).exists():
            return Response(
                {'errors': 'Этот рецепт есть в списке покупок'},
                status=status.HTTP_400_BAD_REQUEST
            )
        return self.shop_fav_post_method(ShoppingCart, user, recipe)

    @shopping_cart.mapping.delete
    def shopping_cart_delete(self, request, pk):
        user = request.user
        recipe = get_object_or_404(Recipe, pk=pk)
        if not ShoppingCart.objects.filter(
            user=user, recipe=recipe
        ).exists():
            return Response(
                {'errors': 'Этого рецепта нет в списке покупок'},
                status=status.HTTP_400_BAD_REQUEST
            )
        return self.shop_fav_delete_method(ShoppingCart, user, recipe)

    @action(
        detail=False, methods=['get'],
        permission_classes=[IsAuthenticated, ])
    def download_shopping_cart(self, request):
        ingredients = (
            RecipeIngredient.objects.filter(
                recipe__shopping_cart__user=request.user
            ).values(
                'ingredient__name',
                'ingredient__measurement_unit'
            ).annotate(
                total_amount=Sum('amount')
            ).order_by(
                'ingredient__name',
                'ingredient__measurement_unit',
            )
        )
        purchase_list = [
            'Список покупок:',
        ]
        for ingredient in ingredients:
            name = ingredient['ingredient__name']
            unit = ingredient['ingredient__measurement_unit']
            total_amount = ingredient['total_amount']
            purchase_list.append(f'{name}: {total_amount}, 'f'{unit}')
        purchase_file = "\n".join(purchase_list)
        response = HttpResponse(purchase_file, content_type='text/plain')
        response[
            'Content-Disposition'
        ] = 'attachment; filename=shopping-list.txt'

        return response

    @action(detail=True, methods=['post',],
            permission_classes=[IsAuthenticated])
    def favorite(self, request, pk):
        user = request.user
        recipe = get_object_or_404(Recipe, pk=pk)
        if Favorite.objects.filter(
            user=user, recipe=recipe
        ).exists():
            return Response(
                {'errors': 'Этот рецепт есть в списке покупок'},
                status=status.HTTP_400_BAD_REQUEST
            )
        return self.shop_fav_post_method(Favorite, user, recipe)

    @favorite.mapping.delete
    def favorite_delete(self, request, pk):
        user = request.user
        recipe = get_object_or_404(Recipe, pk=pk)
        if not Favorite.objects.filter(
            user=user, recipe=recipe
        ).exists():
            return Response(
                {'errors': 'Этого рецепта нет в списке покупок'},
                status=status.HTTP_400_BAD_REQUEST
            )
        return self.shop_fav_delete_method(Favorite, user, recipe)
