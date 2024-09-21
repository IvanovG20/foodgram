from api.filters import RecipeFilter
from api.permissions import IsAuthorOrRead
from api.serializers import (CreateRecipeSerializer, EasyRecipeSerializer,
                             IngredientSerializer, PasswordChangeSerializer,
                             RecipeSerializer, SubscriptionSerializer,
                             TagSerializer, User, UserCreateSerializer,
                             UserSerializer)
from django.db.models import Sum
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from recipes.models import (Favorite, Ingredient, Recipe, RecipeIngredient,
                            ShoppingCart, Tag)
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.filters import SearchFilter
from rest_framework.pagination import LimitOffsetPagination
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet
from users.models import Follow


class UserViewset(ModelViewSet):
    queryset = User.objects.all()
    pagination_class = LimitOffsetPagination

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
        return Response(serializer.data, status=status.HTTP_200_OK)

    @action(
        detail=False, methods=['put', 'delete'],
        permission_classes=[IsAuthenticated],
        url_path='me/avatar'
    )
    def avatar(self, request):
        user = request.user
        if request.method == 'PUT':
            if 'avatar' not in request.data:
                return Response(status=status.HTTP_400_BAD_REQUEST)
            serializer = UserSerializer(
                user, data=request.data, partial=True
            )
            if serializer.is_valid():
                serializer.save()
                url = serializer.data.get('avatar')
                response = {'avatar': url}
                return Response(response, status=status.HTTP_200_OK)
            return Response(
                serializer.errors,
                status=status.HTTP_400_BAD_REQUEST
            )
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
        subs_list = user.follower.all()
        serializer = SubscriptionSerializer(
            self.paginate_queryset(subs_list),
            many=True,
            context={'request': request}
        )
        return self.get_paginated_response(serializer.data)

    @action(detail=True, methods=['post', 'delete'],
            permission_classes=[IsAuthenticated])
    def subscribe(self, request, pk):
        user = self.request.user
        following = get_object_or_404(User, pk=pk)
        if user == following:
            return Response(
                {'errors': 'Нельзя подписаться или отписаться от себя!'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if request.method == 'POST':
            if Follow.objects.filter(
                user=user, following=following
            ).exists():
                return Response(
                    {'errors': 'Подписка уже оформлена!'},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            obj = Follow.objects.create(
                user=user, following=following
            )
            serializer = SubscriptionSerializer(
                obj,
                context={'request': request},
            )
            return Response(
                serializer.data,
                status=status.HTTP_201_CREATED
            )
        if not Follow.objects.filter(
            user=user, following=following
        ).exists():
            return Response(
                {'errors': 'Вы уже отписаны!'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        follow = get_object_or_404(
            Follow, user=user, following=following
        )
        follow.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class TagViewSet(ModelViewSet):
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    pagination_class = None
    http_method_names = ['get']


class IngredientViewSet(ModelViewSet):
    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    pagination_class = None
    http_method_names = ['get']
    filter_backends = [SearchFilter,]
    search_fields = ['^name']


class RecipeViewSet(ModelViewSet):
    queryset = Recipe.objects.all().order_by('-id')
    permission_classes = [IsAuthorOrRead,]
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

    @action(detail=True, methods=['post', 'delete'],
            permission_classes=[IsAuthenticated])
    def shopping_cart(self, request, pk):
        user = request.user
        recipe = get_object_or_404(Recipe, pk=pk)
        if request.method == 'POST':
            if ShoppingCart.objects.filter(
                user=user, recipe=recipe
            ).exists():
                return Response(
                    {'errors': 'Этот рецепт есть в списке покупок'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            ShoppingCart.objects.create(
                user=user, recipe=recipe
            )
            serializer = EasyRecipeSerializer(
                recipe
            )
            return Response(
                serializer.data,
                status=status.HTTP_201_CREATED
            )
        if not ShoppingCart.objects.filter(
            user=user, recipe=recipe
        ).exists():
            return Response(
                {'errors': 'Этого рецепта нет в списке покупок'},
                status=status.HTTP_400_BAD_REQUEST
            )
        ShoppingCart.objects.get(
            user=user, recipe=recipe
        ).delete()
        return Response(
            status=status.HTTP_204_NO_CONTENT
        )

    @action(
        detail=False, methods=['get'],
        permission_classes=[IsAuthenticated,])
    def download_shopping_cart(self, request):
        shopping_cart = ShoppingCart.objects.filter(user=self.request.user)
        recipes = [item.recipe.id for item in shopping_cart]
        buy_objects = (
            RecipeIngredient.objects.filter(recipe__in=recipes)
            .values('ingredient')
            .annotate(amount=Sum('amount'))
        )
        purchase_list = [
            'Список покупок:',
        ]
        for obj in buy_objects:
            ingredient = Ingredient.objects.get(pk=obj['ingredient'])
            amount = obj['amount']
            purchase_list.append(
                f'{ingredient.name}: {amount},'
                f'{ingredient.measurement_unit}'
            )
        purchase_file = "\n".join(purchase_list)

        response = HttpResponse(purchase_file, content_type='text/plain')
        response[
            'Content-Disposition'
        ] = 'attachment; filename=shopping-list.txt'

        return response

    @action(detail=True, methods=['post', 'delete'],
            permission_classes=[IsAuthenticated,])
    def favorite(self, request, pk):
        user = request.user
        recipe = get_object_or_404(Recipe, pk=pk)
        if request.method == 'POST':
            if Favorite.objects.filter(
                user=user, recipe=recipe
            ).exists():
                return Response(
                    {'errors': 'Этот рецепт уже есть в избранном'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            Favorite.objects.create(
                user=user, recipe=recipe
            )
            serializer = EasyRecipeSerializer(
                recipe,
            )
            return Response(
                serializer.data,
                status=status.HTTP_201_CREATED
            )
        if not Favorite.objects.filter(
            user=user, recipe=recipe
        ).exists():
            return Response(
                {'errors': 'Этого рецепта нет в избранном'},
                status=status.HTTP_400_BAD_REQUEST
            )
        Favorite.objects.get(
            user=user, recipe=recipe
        ).delete()
        return Response(
            status=status.HTTP_204_NO_CONTENT
        )
