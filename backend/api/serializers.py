import uuid
import base64

from django.contrib.auth import get_user_model
from django.core.files.base import ContentFile
from rest_framework import serializers
from rest_framework.exceptions import ValidationError

from core.constants import (
    MIN_VALUE_LIMITS,
    MAX_VALUE_LIMITS,
)
from recipes.models import (
    Ingredient,
    Recipe,
    Category,
    RecipeIngredient,
)

User = get_user_model()


class Base64ImageField(serializers.ImageField):
    def to_internal_value(self, data):
        if isinstance(data, str) and data.startswith('data:image'):
            header, base64_data = data.split(';base64,')
            extension = header.split('/')[-1]
            unique_name = f'{uuid.uuid4()}.{extension}'
            decoded_file = ContentFile(
                base64.b64decode(base64_data),
                name=unique_name
            )
            data = decoded_file
        return super().to_internal_value(data)


class UserSerializer(serializers.ModelSerializer):
    is_subscribed = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = (
            'email',
            'id',
            'username',
            'first_name',
            'last_name',
            'is_subscribed',
            'avatar',
        )
        read_only_fields = (
            'email',
            'is_subscribed',
        )

    def get_is_subscribed(self, obj):
        current_user = self.context['request'].user
        if current_user.is_authenticated:
            return current_user.subscription_user.filter(
                author=obj
            ).exists()
        return False


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = (
            'id',
            'title',
            'slug',
        )


class IngredientItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = Ingredient
        fields = (
            'id',
            'name',
            'unit_of_measurement',
        )


class RecipeFavoriteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Recipe
        fields = (
            'id',
            'title',
            'cook_time',
            'image',
        )


class RecipeIngredientSerializer(serializers.ModelSerializer):
    id = serializers.PrimaryKeyRelatedField(
        queryset=Ingredient.objects.all(),
        source='ingredient',
    )
    name = serializers.CharField(
        source='ingredient.name',
        read_only=True,
    )
    unit_of_measurement = serializers.CharField(
        source='ingredient.unit_of_measurement',
        read_only=True,
    )
    quantity = serializers.IntegerField(
        min_value=MIN_VALUE_LIMITS,
        max_value=MAX_VALUE_LIMITS,
    )

    class Meta:
        model = RecipeIngredient
        fields = (
            'id',
            'name',
            'unit_of_measurement',
            'quantity'
        )


class RecipeSerializer(serializers.ModelSerializer):
    categories = CategorySerializer(many=True, read_only=True)
    ingredients = RecipeIngredientSerializer(
        source='recipeingredient_set',
        many=True
    )
    author = UserSerializer(read_only=True)
    is_favorited = serializers.SerializerMethodField(read_only=True)
    is_in_shopping_cart = serializers.SerializerMethodField(read_only=True)
    cook_time = serializers.IntegerField(
        min_value=MIN_VALUE_LIMITS,
        max_value=MAX_VALUE_LIMITS,
    )

    class Meta:
        model = Recipe
        fields = (
            'id',
            'title',
            'description',
            'cook_time',
            'categories',
            'ingredients',
            'author',
            'image',
            'is_favorited',
            'is_in_shopping_cart',
        )

    def get_is_favorited(self, obj):
        author = self.context['request'].user
        return (
            author.is_authenticated
            and author.favorited_by_users.filter(
                recipe=obj
            ).exists()
        )

    def get_is_in_shopping_cart(self, obj):
        author = self.context['request'].user
        return (
            author.is_authenticated
            and author.shopping_items.filter(
                recipe=obj
            ).exists()
        )


class RecipeCreateSerializer(serializers.ModelSerializer):
    categories = serializers.PrimaryKeyRelatedField(
        many=True,
        queryset=Category.objects.all()
    )
    ingredients = RecipeIngredientSerializer(
        source='recipeingredient_set',
        many=True
    )

    author = UserSerializer(read_only=True)
    image = Base64ImageField()
    cook_time = serializers.IntegerField(
        min_value=MIN_VALUE_LIMITS,
        max_value=MAX_VALUE_LIMITS,
    )
    is_favorited = serializers.SerializerMethodField(read_only=True)
    is_in_shopping_cart = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Recipe
        fields = (
            'id',
            'title',
            'description',
            'cook_time',
            'categories',
            'ingredients',
            'author',
            'image',
            'is_favorited',
            'is_in_shopping_cart',
        )

    def validate(self, data):
        self._validate_categories(data.get('categories', []))
        self._validate_ingredients(data.get('recipeingredient_set', []))
        self._validate_image(data.get('image'))
        return data

    def _validate_categories(self, categories):
        if not categories:
            raise ValidationError(
                {'categories': 'Поле Категория не может быть пустым'}
            )

        category_ids = {category.id for category in categories}
        if len(categories) != len(category_ids):
            raise ValidationError(
                {'categories': 'Категории должны быть уникальными'}
            )

    def _validate_ingredients(self, ingredients):
        ingredient_ids = {ing['ingredient'].id for ing in ingredients}
        if len(ingredients) != len(ingredient_ids):
            raise ValidationError(
                {'ingredients': 'Ингредиенты не должны повторяться'}
            )

    def _validate_image(self, image):
        if not image:
            raise ValidationError(
                {'image': 'Необходимо предоставить изображение'}
            )

    def validate_ingredients(self, ingredients_data):
        if not ingredients_data:
            raise ValidationError('Нет ингредиентов')
        return ingredients_data

    def handle_ingredients(self, recipe, ingredients_data):
        recipe.ingredients.clear()
        ingredients_to_create = [
            RecipeIngredient(
                recipe=recipe,
                ingredient=data.pop('ingredient'),
                **data
            )
            for data in ingredients_data
        ]
        RecipeIngredient.objects.bulk_create(ingredients_to_create)

    def create(self, validated_data):
        ingredients_data = self.validate_ingredients(
            validated_data.pop('recipeingredient_set', [])
        )
        categories_data = validated_data.pop('categories', [])
        validated_data['author'] = self.context['request'].user
        recipe = Recipe.objects.create(**validated_data)
        recipe.categories.set(categories_data)
        self.handle_ingredients(recipe, ingredients_data)
        return recipe

    def update(self, instance, validated_data):
        ingredients_data = self.validate_ingredients(
            validated_data.pop('recipeingredient_set', [])
        )
        categories_data = validated_data.pop('categories', [])
        instance = super().update(instance, validated_data)
        instance.categories.set(categories_data)
        self.handle_ingredients(instance, ingredients_data)
        return instance

    def get_is_favorited(self, obj):
        author = self.context['request'].user
        return (
            author.is_authenticated
            and author.favorited_by_users.filter(
                recipe=obj
            ).exists()
        )

    def get_is_in_shopping_cart(self, obj):
        author = self.context['request'].user
        return (
            author.is_authenticated
            and author.shopping_items.filter(
                recipe=obj
            ).exists()
        )

    def to_representation(self, instance):
        return RecipeSerializer(instance, context=self.context).data


class SubscribeSerializer(serializers.ModelSerializer):
    is_subscribed = serializers.SerializerMethodField()
    recipes = serializers.SerializerMethodField()
    recipes_count = serializers.IntegerField(read_only=True)
    avatar = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = (
            'id',
            'email',
            'username',
            'first_name',
            'last_name',
            'is_subscribed',
            'recipes',
            'recipes_count',
            'avatar'
        )
        read_only_fields = fields

    def get_is_subscribed(self, obj):
        user = self.context['request'].user
        return user.is_authenticated and user.subscription_user.filter(
            author=obj
        ).exists()

    def get_recipes(self, obj):
        recipes = obj.recipes.all()
        request = self.context.get('request')
        if request:
            recipes_limit = request.query_params.get('recipes_limit')
            if recipes_limit is not None:
                recipes_limit = int(recipes_limit)
                recipes = recipes[:recipes_limit]
        return RecipeFavoriteSerializer(
            recipes,
            many=True,
            context=self.context
        ).data

    def get_avatar(self, obj):
        return self.context['request'].build_absolute_uri(
            obj.avatar.url
        ) if obj.avatar else None


class UserRegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = (
            'email',
            'id',
            'username',
            'first_name',
            'last_name',
            'password',
        )

    def create(self, validated_data):
        return User.objects.create_user(
            email=validated_data['email'],
            username=validated_data['username'],
            first_name=validated_data['first_name'],
            last_name=validated_data['last_name'],
            password=validated_data['password'],
        )


class AvatarSerializer(serializers.Serializer):
    avatar = serializers.CharField()

    def validate_avatar(self, value):
        try:
            format, imgstr = value.split(';base64,')
            if format.split('/')[0] != 'data:image':
                raise serializers.ValidationError(
                    'Неверный формат изображения'
                )
            return ContentFile(base64.b64decode(imgstr), name='avatar.png')
        except Exception:
            raise serializers.ValidationError(
                'Ошибка при обработке изображения'
            )

    def save(self, **kwargs):
        user = self.context['request'].user
        user.avatar.save(
            self.validated_data['avatar'].name,
            self.validated_data['avatar'], save=True
        )
        return user.avatar.url


class PasswordSerializer(serializers.Serializer):
    current_password = serializers.CharField()
    new_password = serializers.CharField()

    def validate_current_password(self, value):
        user = self.context['request'].user
        if not user.check_password(value):
            raise serializers.ValidationError(
                'Неверный текущий пароль'
            )
        return value

    def save(self, **kwargs):
        user = self.context['request'].user
        user.set_password(self.validated_data['new_password'])
        user.save()
