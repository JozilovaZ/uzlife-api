from rest_framework import permissions


class IsAuthorOrStaffOrReadOnly(permissions.BasePermission):
    """O‘qish hammaga ochiq. Tahrirlash/o‘chirish faqat muallif yoki xodimga."""

    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return True
        return bool(request.user and request.user.is_authenticated)

    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True
        user = request.user
        if user.is_staff:
            return True
        return getattr(obj, 'author_id', None) == user.id
