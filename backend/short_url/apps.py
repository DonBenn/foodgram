from django.apps import AppConfig


class ShortUrlConfig(AppConfig):
    """Конфигурации приложения Короткой ссылки."""

    default_auto_field = 'django.db.models.BigAutoField'
    name = 'short_url'
