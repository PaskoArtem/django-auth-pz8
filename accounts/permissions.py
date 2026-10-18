from rest_framework.permissions import BasePermission, SAFE_METHODS


class IsMethodistOrReadOnly(BasePermission):
    """Авторизованные пользователи читают данные; изменяет только Методист."""

    message = 'Изменять учебные данные может только пользователь группы «Методист».'

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        if request.method in SAFE_METHODS:
            return True
        return request.user.groups.filter(name='Методист').exists()
