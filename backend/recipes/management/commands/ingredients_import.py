import os
from csv import DictReader

from django.conf import settings
from django.core.management.base import BaseCommand

from recipes.models import Ingredient


class Command(BaseCommand):

    def handle(self, *args, **options):
        with open(
                os.path.join(settings.BASE_DIR, 'data/ingredients.csv'),
                'r',
                encoding='utf-8'
        ) as file:
            ingredients = [
                Ingredient(
                    **row
                )
                for row in DictReader(
                    file, fieldnames=('name', 'measurement_unit',)
                )
            ]
            Ingredient.objects.bulk_create(ingredients)
            print('Продукты загружены')
