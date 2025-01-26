from rest_framework.permissions import BasePermission


class IsAuthorOrAdminOnly(BasePermission):
    """Класс в котором проверяется пользователь.

    Проверяется является ли пользователь владельцем объекта,
    разрещая ему редактировать его.
    """

    def has_permission(self, request, view):
        """Метод проверяет аутефецикацию и безопасный метод."""
        return request.user.is_authenticated

    def has_object_permission(self, request, view, obj):
        """Метод проверяет является ли user автором, модератором или админом.

        Безопасный ли метод запроса
        """
        return (
            obj.author == request.user
            or request.user.is_superuser
        )
