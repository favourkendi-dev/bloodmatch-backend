from rest_framework import permissions


class IsAdminRole(permissions.BasePermission):
    """
    Only allows access to users whose role is 'admin'.
    """
    def has_permission(self, request, view):
        return bool(
            request.user
            and request.user.is_authenticated
            and getattr(request.user, 'role', None) == 'admin'
        )
