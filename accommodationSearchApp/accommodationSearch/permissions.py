from rest_framework import permissions
from rest_framework.permissions import SAFE_METHODS


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


class IsLandlordOfRoom(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        # Kiểm tra xem user có phải là chủ trọ của phòng này không
        return request.user == obj.room.motel.user


class IsLandlordOrTenant(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        # Kiểm tra xem user có phải là chủ trọ hoặc người thuê của hợp đồng này không
        return request.user in [obj.room.motel.user, obj.tenant.user]

    def has_permission(self, request, view):
        # Kiểm tra thêm lý do hủy hợp đồng
        if request.method == 'POST':
            reason = request.data.get('reason')
            if not reason:
                self.message = {
                    "error": "Vui lòng cung cấp lý do hủy hợp đồng",
                    "ví_dụ": {
                        "reason": "Không đóng tiền phòng đúng hạn"
                    }
                }
                return False
        return True


class IsAdmin(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user and request.user.is_staff
