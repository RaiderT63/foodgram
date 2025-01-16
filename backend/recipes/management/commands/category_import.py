from csv import DictReader

from django.core.management.base import BaseCommand

from recipes.models import Tag

PATH_CSV = 'data/recipes_tag.csv'


class Command(BaseCommand):

    def handle(self, *args, **options):
        with open(
                PATH_CSV,
                'r',
                encoding='utf-8'
        ) as file:
            categories = [
                Tag(
                    name=row['name'], slug=row['slug']
                )
                for row in DictReader(
                    file, fieldnames=('name', 'slug',)
                )
            ]
            Tag.objects.bulk_create(categories)
            self.stdout.write(self.style.SUCCESS('Data imported successfully'))
