from rest_framework.pagination import PageNumberPagination


class BaseCustomPagination(PageNumberPagination):
    page_size_query_param = 'limit'
    default_page_size = 6
    max_page_size = 100

    def get_page_size(self, request):
        """
        Возвращает количество элементов на странице.
        Использует параметр 'limit', если он указан в запросе.
        """
        if self.page_size_query_param:
            try:
                return int(
                    request.query_params.get(
                        self.page_size_query_param,
                        self.default_page_size
                    )
                )

            except (TypeError, ValueError):
                pass
        return self.default_page_size


class CustomUserPagination(BaseCustomPagination):
    """
    Пагинация для списка пользователей.
    """
    default_page_size = 6
    max_page_size = 50


class CustomRecipePagination(BaseCustomPagination):
    """
    Пагинация для списка рецептов.
    """
    default_page_size = 6
    max_page_size = 50
