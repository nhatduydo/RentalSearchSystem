from rest_framework import permissions
from rest_framework.permissions import SAFE_METHODS


class CommentOwner(permissions.IsAuthenticated):
    def has_object_permission(self, request, view, obj):
        return super().has_permission(request, view) and request.user == obj.user


class IsOwnerOrReadOnly(permissions.IsAuthenticated):
    """
    Cho phép chỉ chủ sở hữu của đối tượng mới có thể chỉnh sửa hoặc xóa
    """

    def has_object_permission(self, request, view, obj):
        if request.method in SAFE_METHODS:
            return True
        return obj.user == request.user


class IsOwnerOrAdmin(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        # Admin có quyền truy cập tất cả
        if request.user.is_staff:
            return True
        # Nếu object có thuộc tính user
        if hasattr(obj, 'user'):
            return request.user == obj.user
        # Nếu object có thuộc tính motel và motel có user
        if hasattr(obj, 'motel') and hasattr(obj.motel, 'user'):
            return request.user == obj.motel.user
        return False
