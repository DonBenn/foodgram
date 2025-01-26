from django.db import models


class ShortLink(models.Model):
    """Настройки модели Короткой ссылки."""

    long_url = models.URLField(unique=True)
    short_url = models.CharField(max_length=3)

    class Meta:
        """Метаданные модели Короткой ссылки."""

        verbose_name = 'Короткая ссылка'
        verbose_name_plural = 'Короткие ссылки'
        ordering = ['long_url']
        constraints = [
            models.UniqueConstraint(
                fields=('long_url', 'short_url'),
                name='long_url_short_url_constraint'
            ),
        ]

    def __str__(self):
        """Возвращает строковое представление объекта."""
        return self.long_url
