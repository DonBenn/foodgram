from django.contrib import admin
from short_url.models import ShortLink

admin.site.empty_value_display = 'Не задано'


class ShortLinkAdmin(admin.ModelAdmin):
    """Настройки админ панели модели Короткой ссылки."""

    list_display = (
        'long_url',
        'short_url'
    )

    search_fields = ('long_url',)
    list_display_links = ('long_url',)


admin.site.register(ShortLink, ShortLinkAdmin)
