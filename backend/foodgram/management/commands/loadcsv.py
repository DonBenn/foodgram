import os
from csv import reader

from django.core.management.base import BaseCommand

from foodgram.models import Ingredient, Tag
from foodgram_backend.settings import BASE_DIR


def load_ingredients(row):
    """Метод создания таблицы ингредиентов."""
    Ingredient.objects.get_or_create(
        name=row[0],
        measurement_unit=row[1]
    )


def load_tags(row):
    """Метод создания таблицы тэгов."""
    Tag.objects.get_or_create(
        name=row[0],
        slug=row[1]
    )


files_functions = (
    ('ingredients.csv', load_ingredients),
    ('tags.csv', load_tags),
)


class Command(BaseCommand):
    help = 'Начало загрузки файлов'

    def handle(self, *args, **options):
        for file, function in files_functions:
            file_path = os.path.join(BASE_DIR, "data", file)
            with open(file_path, 'r', encoding='utf-8') as current_file:
                content = reader(current_file)
                next(content)
                for row in content:
                    function(row)
            self.stdout.write(f'{file} загружен!')
        self.stdout.write('Загрузка завершена')
