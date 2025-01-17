from django.contrib.auth import get_user_model
from django.db.models import Count, Sum
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect
from django_filters.rest_framework import DjangoFilterBackend
from djoser.views import UserViewSet as DjoserUserViewSet
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import (
    AllowAny, IsAuthenticated, IsAuthenticatedOrReadOnly, SAFE_METHODS
)
from rest_framework.response import Response

from recipes.models import (
    FavoriteRecipe, Ingredient, Recipe,
    RecipeIngredient, ShoppingItem, Tag
)
from users.models import UserSubscription

from .filters import IngredientFilter, RecipeFilter
from .paginations import CustomPagination
from .permissions import IsRecipeAuthorOrReadOnly
from .serializers import (
    AvatarSerializer, IngredientItemSerializer,
    RecipeCreateUpdateSerializer, RecipeSerializer,
    SubscribeSerializer, SubscriptionSerializer,
    TagSerializer, WriteFavoriteSerializer,
    WriteShopingItemSerializer, UserSerializer
)

User = get_user_model()


class TagViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
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
        if self.request.method in SAFE_METHODS:
            return RecipeSerializer
        return RecipeCreateUpdateSerializer

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)

    @staticmethod
    def _favorite_shopping_cart_logic(
        request,
        pk,
        model,
        serializer,
    ):
        recipe = get_object_or_404(Recipe, id=pk)
        if request.method == 'DELETE':
            deleted_objects_count, _ = model.objects.filter(
                recipe=pk, user=request.user
            ).delete()
            if deleted_objects_count == 0:
                return Response(status=status.HTTP_400_BAD_REQUEST)
            return Response(status=status.HTTP_204_NO_CONTENT)
        serializer = serializer(
            data={'recipe': recipe.pk, 'user': request.user.pk},
            context={'request': request}
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=('POST', 'DELETE'))
    def favorite(self, request, pk):
        return self._favorite_shopping_cart_logic(
            request,
            pk=pk,
            model=FavoriteRecipe,
            serializer=WriteFavoriteSerializer,
        )

    @action(detail=True, methods=('POST', 'DELETE'))
    def shopping_cart(self, request, pk):
        return self._favorite_shopping_cart_logic(
            request,
            pk=pk,
            model=ShoppingItem,
            serializer=WriteShopingItemSerializer,
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
        serializer.update(user, serializer.validated_data)
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
            deleted_objects_count, _ = UserSubscription.objects.filter(
                subscriber=request.user,
                author=author
            ).delete()
            if deleted_objects_count == 0:
                return Response(status=status.HTTP_400_BAD_REQUEST)
            return Response(status=status.HTTP_204_NO_CONTENT)

        data = {'subscriber': user.id, 'author': author.id}
        serializer = SubscriptionSerializer(data=data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        annotated_author = User.objects.annotate(
            recipes_count=Count('recipes')
        ).get(pk=author.id)
        return_serializer = SubscribeSerializer(
            annotated_author, context={'request': request}
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
