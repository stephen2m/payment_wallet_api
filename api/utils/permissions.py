from rest_framework.permissions import BasePermission, SAFE_METHODS


class BaseAuthPermission(BasePermission):
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_active)


class IsNotAuthenticated(BasePermission):
    """
    Allows access only to non-authenticated users.
    """
    def has_permission(self, request, view):
        return request.user.is_anonymous


class IsActiveAdminUser(BasePermission):
    """
    Allows access only to active admin users
    """

    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and request.user.is_staff and request.user.is_active)

    def has_object_permission(self, request, view, obj):
        return bool(request.user and request.user.is_authenticated and request.user.is_staff and request.user.is_active)


class IsActiveUser(BasePermission):
    """
    Allows access only to active users.
    """

    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and request.user.is_active)


class IsOwner(BaseAuthPermission):
    """
    Object-level permission to allow access only to the user who owns the object being accessed
    """

    def has_object_permission(self, request, view, obj):

        return bool(request.user.is_active and (obj.created_by == request.user))
