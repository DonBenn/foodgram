from django.shortcuts import redirect
from rest_framework import status
from rest_framework.response import Response
from short_url.models import ShortLink


def redirect_url(request, index):
    """Функция перенаправления с короткой ссылки на длинную."""
    try:
        short_url = ShortLink.objects.get(short_url=index)
        return redirect(short_url.long_url, status=status.HTTP_200_OK)
    except ShortLink.DoesNotExist:
        return Response('Не найденно URL', status=status.HTTP_404_NOT_FOUND)
