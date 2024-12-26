from django.contrib.auth import get_user_model
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django.db.models import Sum
from django_filters.rest_framework import (
    FilterSet,
    CharFilter,
    ModelMultipleChoiceFilter,
    ModelChoiceFilter,
    BooleanFilter
)
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.permissions import (
    IsAuthenticated,
    AllowAny,
    IsAuthenticatedOrReadOnly,
)
from rest_framework.response import Response

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
    SubscribeSerializer,
    RecipeShortSerializer,
)

from recipes.models import (
    Category,
    Ingredient,
    Recipe,
    FavoriteRecipe,
    ShoppingItem,
    RecipeIngredient,
)
from core.paginations import (
    CustomUserPagination,
    CustomRecipePagination,
)
from core.permissions import (
    IsRecipeAuthorOrReadOnly,
)
from users.models import UserSubscription

User = get_user_model()


class CategoryViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    pagination_class = None


class IngredientFilter(FilterSet):
    name = CharFilter(field_name='name', lookup_expr='istartswith')

    class Meta:
        model = Ingredient
        fields = ['name']


class IngredientViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Ingredient.objects.all().order_by('name')
    serializer_class = IngredientItemSerializer
    permission_classes = [AllowAny]
    pagination_class = None
    filter_backends = [DjangoFilterBackend]
    filterset_class = IngredientFilter


class RecipeFilter(FilterSet):
    tags = ModelMultipleChoiceFilter(
        field_name='tags__slug',
        to_field_name='slug',
        queryset=Category.objects.all()
    )
    author = ModelChoiceFilter(
        field_name='author',
        queryset=User.objects.all()
    )
    is_in_shopping_cart = BooleanFilter(method='filter_is_in_shopping_cart')
    is_favorited = BooleanFilter(method='filter_is_favorited')

    class Meta:
        model = Recipe
        fields = ['tags', 'author', 'is_in_shopping_cart', 'is_favorited']

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
    serializer_class = RecipeSerializer
    permission_classes = [IsAuthenticatedOrReadOnly, IsRecipeAuthorOrReadOnly]
    pagination_class = CustomRecipePagination
    filter_backends = (DjangoFilterBackend,)
    filterset_class = RecipeFilter

    def get_queryset(self):
        queryset = Recipe.objects.all()
        author = self.request.query_params.get('author')
        if author:
            queryset = queryset.filter(author=author)
        return queryset

    def get_serializer_class(self):
        if self.action in ('create', 'partial_update'):
            return RecipeCreateSerializer
        return RecipeSerializer

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)

    @action(
        detail=True,
        methods=['post', 'delete'],
        permission_classes=[IsAuthenticated]
    )
    def favorite(self, request, pk):
        recipe = get_object_or_404(Recipe, id=pk)
        favorite = FavoriteRecipe.objects.filter(
            user=request.user,
            recipe=recipe
        )

        if request.method == 'POST':
            if favorite.exists():
                return Response(
                    {'errors': 'Рецепт уже в избранном'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            FavoriteRecipe.objects.create(
                user=request.user,
                recipe=recipe
            )
            serializer = RecipeFavoriteSerializer(recipe)
            return Response(
                serializer.data,
                status=status.HTTP_201_CREATED
            )

        if not favorite.exists():
            return Response(
                {'errors': 'Рецепт не найден в избранном'},
                status=status.HTTP_400_BAD_REQUEST
            )
        favorite.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(
        detail=True,
        methods=['post', 'delete'],
        permission_classes=[IsAuthenticated]
    )
    def shopping_cart(self, request, pk):
        recipe = get_object_or_404(Recipe, id=pk)
        shopping_item = ShoppingItem.objects.filter(
            user=request.user,
            recipe=recipe
        )

        if request.method == 'POST':
            if shopping_item.exists():
                return Response(
                    {'errors': 'Рецепт уже добавлен в корзину'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            ShoppingItem.objects.create(
                user=request.user,
                recipe=recipe
            )
            serializer = RecipeShortSerializer(recipe)
            return Response(
                serializer.data,
                status=status.HTTP_201_CREATED
            )

        if not shopping_item.exists():
            return Response(
                {'errors': 'Рецепт не найден в корзине'},
                status=status.HTTP_400_BAD_REQUEST
            )
        shopping_item.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(
        detail=False,
        methods=['get'],
        permission_classes=[IsAuthenticated]
    )
    def download_shopping_cart(self, request):
        user = request.user
        ingredients = (
            RecipeIngredient.objects.filter(
                recipe__in_users_shopping_list__user=user
            ).values(
                'ingredient__name',
                'ingredient__measurement_unit'
            ).annotate(total=Sum('amount'))
        )

        shopping_list = []
        for ingredient in ingredients:
            shopping_list.append(
                f"{ingredient['ingredient__name']} "
                f"({ingredient['ingredient__measurement_unit']}) - "
                f"{ingredient['total']}"
            )

        response = HttpResponse(
            'Список покупок:\n' + '\n'.join(shopping_list),
            content_type='text/plain'
        )
        response['Content-Disposition'] = (
            'attachment; filename="shopping_list.txt"'
        )
        return response

    @action(detail=True, methods=['get'], url_path='get-link')
    def get_short_link(self, request, pk=None):
        recipe = self.get_object()
        short_link = f"/r/{recipe.id}"
        return Response({'short-link': short_link})


class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    pagination_class = CustomUserPagination

    def get_permissions(self):
        if self.action in ['create', 'list', 'retrieve']:
            return [AllowAny()]
        return [IsAuthenticated()]

    def get_serializer_class(self):
        if self.action == 'create':
            return UserRegisterSerializer
        return UserSerializer

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context.update({'request': self.request})
        return context

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(
            serializer.data,
            status=status.HTTP_201_CREATED,
            headers=headers
        )

    @action(
        detail=False,
        methods=['get'],
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

    @action(
        detail=True,
        methods=['post', 'delete'],
        permission_classes=[IsAuthenticated]
    )
    def subscribe(self, request, pk):
        author = get_object_or_404(User, id=pk)
        subscription = UserSubscription.objects.filter(
            subscriber=request.user,
            author=author
        )

        if request.method == 'POST':
            if request.user == author:
                return Response(
                    {'errors': 'Нельзя подписаться на самого себя'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            if subscription.exists():
                return Response(
                    {'errors': 'Вы уже подписаны на этого пользователя'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            UserSubscription.objects.create(
                subscriber=request.user,
                author=author
            )
            serializer = SubscribeSerializer(
                author,
                context={'request': request}
            )
            return Response(
                serializer.data,
                status=status.HTTP_201_CREATED
            )

        if not subscription.exists():
            return Response(
                {'errors': 'Вы не подписаны на этого пользователя'},
                status=status.HTTP_400_BAD_REQUEST
            )
        subscription.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(
        detail=False,
        methods=['get'],
        permission_classes=[IsAuthenticated]
    )
    def subscriptions(self, request):
        queryset = User.objects.filter(
            subscriptions__subscriber=request.user
        )

        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = SubscribeSerializer(
                page,
                many=True,
                context={'request': request}
            )
            return self.get_paginated_response(serializer.data)

        serializer = SubscribeSerializer(
            queryset,
            many=True,
            context={'request': request}
        )
        return Response(serializer.data)
