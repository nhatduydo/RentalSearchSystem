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
        if request.user.is_staff:
            return True
        if hasattr(obj, 'user'):
            return request.user == obj.user
        if hasattr(obj, 'motel') and hasattr(obj.motel, 'user'):
            return request.user == obj.motel.user
        return False


class IsLandlordOfRoom(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        return request.user == obj.room.motel.user


class IsLandlordOrTenant(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
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


class IsPaymentOwnerOrMotelOwner(permissions.BasePermission):
    """
    Cho phép:
    1. Admin truy cập tất cả payment
    2. Người thanh toán (payer) truy cập payment của họ
    3. Chủ nhà truy cập tất cả payment của phòng trong motel của họ
    4. Người thuê phòng truy cập payment của phòng họ đang thuê
    """

    def has_object_permission(self, request, view, obj):
        if request.user.is_staff:
            return True

        if obj.room.motel.user == request.user:
            return True

        if obj.payer == request.user:
            return True

        try:
            room_tenants = obj.room.room_tenants.filter(
                status='ACTIVE',
                active=True
            ).select_related('tenant__user')

            # Kiểm tra xem người dùng hiện tại có trong danh sách người thuê không
            return any(room_tenant.tenant.user == request.user for room_tenant in room_tenants)
        except Exception:
            return False
