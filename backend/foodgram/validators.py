import re

from django.core.exceptions import ValidationError


def validate_username(value):
    """Метод валидации поля username."""
    if value == 'me':
        raise ValidationError(
            ('Имя пользователя не может быть <me>.'),
            params={'value': value},
        )
    if re.search(r'^[\w.@+-]+\Z', value) is None:
        raise ValidationError(
            (f'Недопустимые символы <{value}> в username.'),
            params={'value': value},
        )
