from django.contrib.auth import get_user_model
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect
from django.db.models import Sum, Count
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import viewsets, status
from rest_framework.exceptions import ValidationError
from rest_framework.decorators import action
from rest_framework.permissions import (
    IsAuthenticated,
    AllowAny,
    IsAuthenticatedOrReadOnly,
)
from rest_framework.response import Response
from djoser.views import UserViewSet as DjoserUserViewSet

from .serializers import (
    CategorySerializer,
    RecipeSerializer,
    UserSerializer,
    SubscribeSerializer,
    RecipeShortSerializer,
    RecipeCreateUpdateSerializer,
    IngredientItemSerializer,
    AvatarSerializer,
    SubscriptionSerializer,
)
from recipes.models import (
    Category,
    Ingredient,
    Recipe,
    FavoriteRecipe,
    ShoppingItem,
    RecipeIngredient,
)
from .paginations import CustomPagination
from .permissions import IsRecipeAuthorOrReadOnly
from users.models import UserSubscription
from .filters import IngredientFilter, RecipeFilter

User = get_user_model()


class CategoryViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    pagination_class = None


class IngredientViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Ingredient.objects.all().order_by('name')
    serializer_class = IngredientItemSerializer
    permission_classes = [AllowAny]
    pagination_class = None
    filter_backends = [DjangoFilterBackend]
    filterset_class = IngredientFilter


class RecipeViewSet(viewsets.ModelViewSet):
    serializer_class = RecipeSerializer
    permission_classes = [IsAuthenticatedOrReadOnly, IsRecipeAuthorOrReadOnly]
    pagination_class = CustomPagination
    filter_backends = (DjangoFilterBackend,)
    filterset_class = RecipeFilter

    def get_queryset(self):
        return Recipe.objects.select_related(
            'author'
        ).prefetch_related(
            'tags',
            'recipe_ingredients__ingredient'
        )

    def get_serializer_class(self):
        if self.action in ('create', 'partial_update'):
            return RecipeCreateUpdateSerializer
        return RecipeSerializer

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)

    @staticmethod
    def _favorite_shopping_cart_logic(
        request,
        error_message_add,
        pk,
        model,
    ):
        recipe = get_object_or_404(Recipe, pk=pk)
        if request.method == "DELETE":
            obj = model.objects.filter(
                recipe=recipe, user=request.user
            ).first()
            if not obj:
                return Response(status=status.HTTP_400_BAD_REQUEST)
            obj.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        item, created = model.objects.get_or_create(
            user=request.user, recipe=recipe
        )
        if not created:
            raise ValidationError(dict(error=error_message_add))
        return Response(
            RecipeShortSerializer(recipe).data,
            status=status.HTTP_201_CREATED,
        )

    @action(detail=True, methods=("POST", "DELETE"))
    def favorite(self, request, pk):
        return self._favorite_shopping_cart_logic(
            request,
            error_message_add='Уже есть в избранном',
            pk=pk,
            model=FavoriteRecipe,
        )

    @action(detail=True, methods=("POST", "DELETE"))
    def shopping_cart(self, request, pk):
        return self._favorite_shopping_cart_logic(
            request,
            error_message_add='Уже есть в корзине',
            pk=pk,
            model=ShoppingItem,
        )

    def create_shopping_list(self, ingredients):
        shopping_list = ['Список покупок:']

        for ingredient in ingredients:
            shopping_list.append(
                f"{ingredient['ingredient__name']} "
                f"({ingredient['ingredient__measurement_unit']}) - "
                f"{ingredient['total']}"
            )

        return '\n'.join(shopping_list)

    @action(
        detail=False,
        methods=['get'],
        permission_classes=[IsAuthenticated]
    )
    def download_shopping_cart(self, request):
        ingredients = (
            RecipeIngredient.objects.filter(
                recipe__in_users_shopping_list__user=request.user
            ).values(
                'ingredient__name',
                'ingredient__measurement_unit'
            ).annotate(total=Sum('amount'))
        )

        shopping_list = self.create_shopping_list(ingredients)

        response = HttpResponse(
            shopping_list,
            content_type='text/plain'
        )
        response['Content-Disposition'] = (
            'attachment; filename="shopping_list.txt"'
        )
        return response

    @action(detail=True, methods=['get'], url_path='get-link')
    def get_short_link(self, request, pk=None):
        return Response({'short-link': request.build_absolute_uri(
            self.get_object().get_absolute_url()
        )})


class UserViewSet(DjoserUserViewSet):
    serializer_class = UserSerializer
    pagination_class = CustomPagination

    def get_permissions(self):
        if self.action in ['create', 'list', 'retrieve']:
            return [AllowAny()]
        return [IsAuthenticated()]

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
        detail=False,
        methods=['put', 'delete'],
        permission_classes=[IsAuthenticated],
        url_path='me/avatar'
    )
    def avatar(self, request):
        user = request.user
        if request.method == 'DELETE':
            user.avatar.delete(save=True)
            return Response(status=status.HTTP_204_NO_CONTENT)
        serializer = AvatarSerializer(data=request.data,)
        serializer.is_valid(raise_exception=True)
        user.avatar = serializer.validated_data['avatar']
        user.save()
        return Response(
            AvatarSerializer(user).data,
            status=status.HTTP_200_OK
        )

    @action(
        detail=True,
        methods=['post', 'delete'],
        permission_classes=[IsAuthenticated],
        url_path='subscribe'
    )
    def subscribe(self, request, id):
        user = request.user
        author = get_object_or_404(User, pk=id)
        if request.method == 'DELETE':
            obj = UserSubscription.objects.filter(
                subscriber=request.user,
                author=author
            ).delete()
            if obj[0] == 0:
                return Response(status=status.HTTP_400_BAD_REQUEST)
            return Response(status=status.HTTP_204_NO_CONTENT)

        data = {'subscriber': user.id, 'author': author.id}
        serializer = SubscriptionSerializer(data=data)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return_serializer = SubscribeSerializer(
            author, context={'request': request}
        )
        return Response(
            return_serializer.data, status=status.HTTP_201_CREATED
        )

    @action(
        detail=False,
        methods=['get'],
        permission_classes=[IsAuthenticated]
    )
    def subscriptions(self, request):
        queryset = User.objects.filter(
            subscribed_by__subscriber=request.user
        ).annotate(
            recipes_count=Count('recipes')
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


def short_link_view(request, pk):
    return redirect('api:recipes-detail', pk=pk)
