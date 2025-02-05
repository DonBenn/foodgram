import random
import string

from django.urls import reverse

from short_url.models import ShortLink
from foodgram.constants import MAX_SHORT_URL_LENGTH


def generate_short_url():
    """Функция генерации короткой ссылки рецепта."""
    letters_digits = string.digits + string.ascii_letters
    while True:
        short_url = ''.join(
            random.choice(letters_digits) for element in range(
                MAX_SHORT_URL_LENGTH
            )
        )
        if not ShortLink.objects.filter(short_url=short_url).exists():
            return short_url


def get_new_url(request, id):
    long_url = request.build_absolute_uri(
        reverse('recipes-detail', args=[id])
    ).replace('api/', '')
    short_url = generate_short_url()
    url, created = ShortLink.objects.get_or_create(long_url=long_url)
    if not created:
        new_url = request.build_absolute_uri(
            reverse('redirect_url', args=[url.short_url])
        )
        return new_url
    url.short_url = short_url
    url.save()
    new_url = request.build_absolute_uri(
        reverse('redirect_url', args=[url.short_url])
    )
    return new_url
