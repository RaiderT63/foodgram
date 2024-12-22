from django.contrib.auth import get_user_model
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django.db.models import F, Sum
from django_filters.rest_framework import (
    FilterSet,
    CharFilter,
    ModelMultipleChoiceFilter,
    ModelChoiceFilter,
    BooleanFilter
)
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.permissions import (
    IsAuthenticated,
    AllowAny,
    IsAuthenticatedOrReadOnly,
)
from rest_framework.response import Response
import csv

from .serializers import (
    CategorySerializer,
    RecipeSerializer,
    RecipeFavoriteSerializer,
    RecipeCreateSerializer,
    UserSerializer,
    UserRegisterSerializer,
    AvatarSerializer,
    PasswordSerializer,
    IngredientItemSerializer,
)

from recipes.models import (
    Category,
    Ingredient,
    Recipe,
    FavoriteRecipe,
    ShoppingItem,
)
from core.paginations import (
    CustomUserPagination,
    CustomRecipePagination,
)
from core.permissions import (
    IsRecipeAuthorOrReadOnly,
    IsProfileOwnerOrReadOnly,
)

User = get_user_model()


class CategoryViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer


class IngredientFilter(FilterSet):
    name = CharFilter(field_name='name', lookup_expr='istartswith')

    class Meta:
        model = Ingredient
        fields = ['name']


class IngredientViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Ingredient.objects.all()
    permission_classes = [IsAuthenticatedOrReadOnly]
    serializer_class = IngredientItemSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_class = IngredientFilter


class RecipeFilter(FilterSet):
    categories = ModelMultipleChoiceFilter(
        field_name='categories__slug',
        to_field_name='slug',
        queryset=Category.objects.all()
    )
    author = ModelChoiceFilter(
        field_name='creator',
        queryset=User.objects.all()
    )
    is_in_shopping_cart = BooleanFilter(method='filter_is_in_shopping_cart')
    is_favorited = BooleanFilter(method='filter_is_favorited')

    class Meta:
        model = Recipe
        fields = [
            'categories',
            'author',
            'is_in_shopping_cart',
            'is_favorited'
        ]

    def filter_is_favorited(self, queryset, name, value):
        if value and not self.request.user.is_anonymous:
            return queryset.filter(favorited_by_users__user=self.request.user)
        return queryset

    def filter_is_in_shopping_cart(self, queryset, name, value):
        if value and not self.request.user.is_anonymous:
            return queryset.filter(
                in_users_shopping_list__user=self.request.user
            )
        return queryset


class RecipeViewSet(viewsets.ModelViewSet):
    queryset = Recipe.objects.all()
    permission_classes = [IsAuthenticatedOrReadOnly, IsRecipeAuthorOrReadOnly]
    pagination_class = CustomRecipePagination
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_class = RecipeFilter
    search_fields = ['title']

    def get_serializer_class(self):
        if self.action in ['list', 'retrieve']:
            return RecipeSerializer
        if self.action in ['create', 'update', 'partial_update']:
            return RecipeCreateSerializer
        return super().get_serializer_class()

    def perform_create(self, serializer):
        serializer.save(creator=self.request.user)

    @action(
        detail=True,
        methods=['post', 'delete'],
        permission_classes=[IsAuthenticated]
    )
    def favorite(self, request, pk=None):
        recipe = get_object_or_404(Recipe, pk=pk)
        user = request.user

        if request.method == 'POST':
            if user.favorite_recipes.filter(recipe=recipe).exists():
                return Response(
                    {'error': 'Рецепт уже в избранном'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            FavoriteRecipe.objects.create(user=user, recipe=recipe)
            serializer = RecipeFavoriteSerializer(recipe)
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        if request.method == 'DELETE':
            favorite_item = user.favorite_recipes.filter(recipe=recipe).first()
            if not favorite_item:
                return Response(
                    {'error': 'Рецепт не найден в избранном'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            favorite_item.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)

    @action(
        detail=True, methods=['post', 'delete'],
        permission_classes=[IsAuthenticated]
    )
    def shopping_cart(self, request, pk=None):
        recipe = get_object_or_404(Recipe, pk=pk)
        user = request.user

        if request.method == 'POST':
            if user.shopping_cart.filter(recipe=recipe).exists():
                return Response(
                    {'error': 'Рецепт уже в корзине'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            ShoppingItem.objects.create(user=user, recipe=recipe)
            serializer = RecipeFavoriteSerializer(recipe)
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        if request.method == 'DELETE':
            cart_item = user.shopping_cart.filter(recipe=recipe).first()
            if not cart_item:
                return Response(
                    {'error': 'Рецепт не найден в корзине'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            cart_item.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)

    @action(
        detail=False, methods=['get'],
        permission_classes=[IsAuthenticated]
    )
    def download_shopping_cart(self, request):
        user = request.user
        ingredients = (
            ShoppingItem.objects
            .filter(user=user)
            .values(
                name=F('recipe__recipeingredient__ingredient__name'),
                unit=F(
                    'recipe__recipeingredient__ingredient__'
                    'unit_of_measurement'
                )
            )
            .annotate(amount=Sum('recipe__recipeingredient__quantity'))
        )

        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = (
            'attachment; filename="shopping_cart.csv"'
        )
        writer = csv.writer(response)
        writer.writerow(['Ингредиент', 'Количество', 'Единица измерения'])
        for item in ingredients:
            writer.writerow([item['name'], item['amount'], item['unit']])
        return response


class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    pagination_class = CustomUserPagination
    permission_classes = [IsAuthenticated]

    def get_permissions(self):
        if self.action == 'create':
            self.permission_classes = [AllowAny]
        elif self.action in ['me', 'avatar', 'set_password']:
            self.permission_classes = [IsProfileOwnerOrReadOnly]
        else:
            self.permission_classes = [IsAuthenticatedOrReadOnly]
        return super().get_permissions()

    def get_serializer_class(self):
        if self.action == 'create':
            return UserRegisterSerializer
        return UserSerializer

    @action(
        detail=False, methods=['get'],
        permission_classes=[IsAuthenticated]
    )
    def me(self, request):
        serializer = self.get_serializer(request.user)
        return Response(serializer.data)

    @action(
        detail=False, methods=['put', 'delete'],
        permission_classes=[IsAuthenticated], url_path='me/avatar'
    )
    def avatar(self, request):
        if request.method == 'PUT':
            serializer = AvatarSerializer(
                data=request.data, context={'request': request}
            )
            serializer.is_valid(raise_exception=True)
            avatar_url = serializer.save()
            return Response({'avatar': avatar_url}, status=status.HTTP_200_OK)
        if request.method == 'DELETE':
            user = request.user
            if not user.avatar:
                return Response(
                    {'error': 'Аватар отсутствует'},
                    status=status.HTTP_404_NOT_FOUND
                )
            user.avatar.delete(save=True)
            return Response(status=status.HTTP_204_NO_CONTENT)

    @action(
        detail=False, methods=['post'],
        permission_classes=[IsAuthenticated]
    )
    def set_password(self, request):
        serializer = PasswordSerializer(
            data=request.data,
            context={'request': request}
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(status=status.HTTP_204_NO_CONTENT)
