from rest_framework import serializers
from django.contrib.auth import get_user_model
from drf_extra_fields.fields import Base64ImageField

from django.shortcuts import get_object_or_404

from recipes.models import (Tag, Ingredient, Recipe,
                            Favorite, ShoppingCart,
                            RecipeIngredient, RecipeTag)

from users.models import Follow


User = get_user_model()


class UserCreateSerializer(serializers.ModelSerializer):

    class Meta:
        model = User
        fields = (
            'email', 'username', 'first_name',
            'last_name', 'password', 'avatar'
        )
        extra_kwargs = {
            'password': {'write_only': True},
            'avatar': {'required': False},
        }

    def create(self, validated_data):
        user = User(
            email=self.validated_data['email'],
            username=self.validated_data['username'],
            first_name=self.validated_data['first_name'],
            last_name=self.validated_data['last_name']
        )
        user.set_password(self.validated_data['password'])
        user.save()
        return user

    def to_representation(self, instance):
        return {
            'email': instance.email,
            'id': instance.id,
            'username': instance.username,
            'first_name': instance.first_name,
            'last_name': instance.last_name
        }


class UserSerializer(serializers.ModelSerializer):
    is_subscribed = serializers.SerializerMethodField(read_only=True)
    avatar = Base64ImageField(required=False, allow_null=True)

    class Meta:
        model = User
        fields = (
            'email', 'id', 'username', 'first_name',
            'last_name', 'is_subscribed', 'avatar'
        )

    def get_is_subscribed(self, obj):
        request = self.context.get('request')
        if request:
            user = self.context.get('request').user
            if user.is_authenticated:
                return user.follower.filter(user=obj).exists()
        return False


class PasswordChangeSerializer(serializers.Serializer):
    new_password = serializers.CharField(write_only=True)
    current_password = serializers.CharField(write_only=True)

    def validate(self, attrs):
        user = self.context['request'].user
        if not user.check_password(attrs['current_password']):
            raise serializers.ValidationError()
        return attrs

    def save(self):
        user = self.context['request'].user
        new_password = self.validated_data['new_password']
        user.set_password(new_password)
        user.save()
        return user


class TagSerializer(serializers.ModelSerializer):

    class Meta:
        model = Tag
        fields = ('id', 'name', 'slug')


class IngredientSerializer(serializers.ModelSerializer):

    class Meta:
        model = Ingredient
        fields = ('id', 'name', 'measurement_unit')


class IngredientRecipeSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(source='ingredient.id')
    name = serializers.CharField(source='ingredient.name')
    measurement_unit = serializers.CharField(
        source='ingredient.measurement_unit'
    )

    class Meta:
        model = RecipeIngredient
        fields = (
            'id', 'name',
            'measurement_unit', 'amount',
        )


class AddIngredientInRecipeSerializer(serializers.ModelSerializer):
    id = serializers.PrimaryKeyRelatedField(
        queryset=Ingredient.objects.all()
    )
    amount = serializers.IntegerField()

    class Meta:
        model = RecipeIngredient
        fields = ('id', 'amount')


class RecipeSerializer(serializers.ModelSerializer):
    tags = TagSerializer(
        many=True, read_only=True
    )
    ingredients = IngredientRecipeSerializer(
        many=True, read_only=True, source='ingredient'
    )
    is_favorited = serializers.SerializerMethodField()
    is_in_shopping_cart = serializers.SerializerMethodField()
    image = Base64ImageField()
    author = UserSerializer(read_only=True)

    class Meta:
        model = Recipe
        fields = (
            'id', 'tags', 'author', 'ingredients',
            'is_favorited', 'is_in_shopping_cart',
            'name', 'image', 'text', 'cooking_time',
        )

    def get_is_favorited(self, obj):
        request = self.context.get('request')
        if request is None:
            return False
        user = request.user
        if user.is_anonymous:
            return False
        return Favorite.objects.filter(
            recipe=obj,
            user=user
        ).exists()

    def get_is_in_shopping_cart(self, obj):
        request = self.context.get('request')
        if request is None:
            return False
        user = request.user
        if user.is_anonymous:
            return False
        return ShoppingCart.objects.filter(
            recipe=obj,
            user=user
        ).exists()


class EasyRecipeSerializer(serializers.ModelSerializer):

    class Meta:
        model = Recipe
        fields = (
            'id', 'name',
            'image', 'cooking_time'
        )


class CreateRecipeSerializer(serializers.ModelSerializer):
    tags = serializers.ListField(
        allow_empty=False,
        required=True,
    )
    ingredients = AddIngredientInRecipeSerializer(
        many=True,
        required=True
    )
    image = Base64ImageField()

    class Meta:
        model = Recipe
        fields = (
            'ingredients', 'tags', 'image',
            'name', 'text', 'cooking_time'
        )

    def validate(self, data):
        if 'ingredients' not in data:
            raise serializers.ValidationError()
        ingredients = data.get('ingredients')
        if 'tags' not in data:
            raise serializers.ValidationError()
        tags = data.get('tags')
        image = data.get('image')
        cooking_time = data.get('cooking_time')
        if cooking_time < 1:
            raise serializers.ValidationError(
                'Время готовки не может быть меньше минуты'
            )
        if image is None:
            raise serializers.ValidationError(
                'Изображение обязательное для создания рецепта'
            )
        if len(ingredients) == 0:
            raise serializers.ValidationError(
                'Список ингредиентов не может быть пустым!'
            )
        ing_list = []
        for ingredient in ingredients:
            id = ingredient.get('id')
            if ingredient.get('amount') < 1:
                raise serializers.ValidationError(
                    'Количество ингредиента не может быть меньше 1'
                )
            if id not in ing_list:
                ing_list.append(id)
            else:
                raise serializers.ValidationError(
                    'Ингредиенты не могут повторяться'
                )
        tag_list = []
        for tag_id in tags:
            if tag_id not in tag_list:
                tag_list.append(tag_id)
            else:
                raise serializers.ValidationError(
                    'Теги не должны повторяться'
                )
            if not Tag.objects.filter(id=tag_id).exists():
                raise serializers.ValidationError(
                    'Невозможно поставить несуществующий тег'
                )
        return data

    def create(self, validated_data):
        ingredients = validated_data.pop('ingredients')
        tags = validated_data.pop('tags')
        recipe = Recipe.objects.create(**validated_data)
        for ingredient in ingredients:
            current_ingredient = ingredient.get('id')
            _, _ = RecipeIngredient.objects.get_or_create(
                ingredient=current_ingredient,
                amount=ingredient.get('amount'),
                recipe=recipe
            )
        for tag_id in tags:
            tag = get_object_or_404(
                Tag, pk=tag_id
            )
            _, _ = RecipeTag.objects.get_or_create(
                recipe=recipe,
                tag=tag
            )
        return recipe

    def to_representation(self, instance):
        serializer = RecipeSerializer(instance)
        return serializer.data


class SubscriptionSerializer(serializers.ModelSerializer):
    email = serializers.ReadOnlyField(source='following.email')
    id = serializers.ReadOnlyField(source='following.id')
    username = serializers.ReadOnlyField(source='following.username')
    first_name = serializers.ReadOnlyField(source='following.first_name')
    last_name = serializers.ReadOnlyField(source='following.last_name')
    is_subscribed = serializers.SerializerMethodField()
    recipes = serializers.SerializerMethodField()
    recipes_count = serializers.SerializerMethodField()
    avatar = Base64ImageField(source='following.avatar')

    class Meta:
        model = Follow
        fields = (
            'email', 'id', 'username', 'first_name',
            'last_name', 'is_subscribed', 'recipes',
            'recipes_count', 'avatar'
        )

    def get_is_subscribed(self, obj):
        request = self.context.get('request')
        if request:
            user = request.user
            if user.is_authenticated:
                return Follow.objects.filter(
                    following=obj.following.id, user=user.id
                ).exists()
        return False

    def get_recipes(self, obj):
        request = self.context.get('request')
        if request:
            recipes_limit = request.guery_params.get('recipes_limit')
            if recipes_limit:
                recipes = recipes = obj.following.recipes.all()[:recipes_limit]
            else:
                recipes = obj.following.recipes.all()
            if recipes:
                serializer = EasyRecipeSerializer(
                    recipes,
                    many=True
                )
                return serializer.data
        return []

    def get_recipes_count(self, obj):
        return obj.following.recipes.count()
