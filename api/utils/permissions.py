from rest_framework.permissions import BasePermission, SAFE_METHODS


class BaseAuthPermission(BasePermission):
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_active)


class IsOwnerOrReadOnly(BaseAuthPermission):
    """
    Object-level permission to only allow owners of an object to edit it.
    Assumes the model instance has a `created_by` attribute.
    Will allow all "safe" methods ie GET, HEAD, OPTIONS
    """

    def has_object_permission(self, request, view, obj):
        # Read permissions are allowed to any request,
        # so we'll always allow GET, HEAD or OPTIONS requests.
        if request.method in SAFE_METHODS:
            return True

        # Instance must have an attribute named `created_by`.
        return bool((obj.created_by == request.user) and request.user.is_active)


class IsOwnerOrStaff(BaseAuthPermission):
    """
    Object-level permission to allow access only to active staff users
    or the user who owns the object being accessed
    """

    def has_object_permission(self, request, view, obj):

        return bool(request.user.is_active and (obj.created_by == request.user) or request.user.is_staff)


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


class IsAuthenticatedUser(BaseAuthPermission):
    """
    Object-level permission to allow access only to the user who owns the object being accessed
    """

    def has_object_permission(self, request, view, obj):

        return request.user.is_authenticated
