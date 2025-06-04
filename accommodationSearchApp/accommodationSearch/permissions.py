from rest_framework import permissions
from rest_framework.permissions import SAFE_METHODS


class IsOwnerOrReadOnly(permissions.IsAuthenticated):
    """
    Permission class cho phép chỉ chủ sở hữu của đối tượng mới có thể chỉnh sửa hoặc xóa
    Kế thừa từ IsAuthenticated để đảm bảo người dùng đã đăng nhập
    """

    def has_object_permission(self, request, view, obj):
        """
        Kiểm tra quyền truy cập đối tượng
        Args:
            request: HTTP request
            view: View đang xử lý request
            obj: Đối tượng cần kiểm tra quyền
        Returns:
            bool: True nếu có quyền, False nếu không
        """
        if request.method in SAFE_METHODS:
            return True
        return obj.user == request.user


class IsOwnerOrAdmin(permissions.BasePermission):
    """
    Permission class cho phép chủ sở hữu hoặc admin truy cập đối tượng
    """

    def has_object_permission(self, request, view, obj):
        """
        Kiểm tra quyền truy cập đối tượng
        Args:
            request: HTTP request
            view: View đang xử lý request
            obj: Đối tượng cần kiểm tra quyền
        Returns:
            bool: True nếu có quyền, False nếu không
        """
        if request.user.is_staff:
            return True
        if hasattr(obj, 'user'):
            return request.user == obj.user
        if hasattr(obj, 'motel') and hasattr(obj.motel, 'user'):
            return request.user == obj.motel.user
        return False


class IsLandlordOfRoom(permissions.BasePermission):
    """
    Permission class cho phép chủ nhà của phòng truy cập đối tượng
    """

    def has_object_permission(self, request, view, obj):
        """
        Kiểm tra quyền truy cập đối tượng
        Args:
            request: HTTP request
            view: View đang xử lý request
            obj: Đối tượng cần kiểm tra quyền
        Returns:
            bool: True nếu có quyền, False nếu không
        """
        return request.user == obj.room.motel.user


class IsLandlordOrTenant(permissions.BasePermission):
    """
    Permission class cho phép chủ nhà hoặc người thuê phòng truy cập đối tượng
    """

    def has_object_permission(self, request, view, obj):
        """
        Kiểm tra quyền truy cập đối tượng
        Args:
            request: HTTP request
            view: View đang xử lý request
            obj: Đối tượng cần kiểm tra quyền
        Returns:
            bool: True nếu có quyền, False nếu không
        """
        return request.user in [obj.room.motel.user, obj.tenant.user]

    def has_permission(self, request, view):
        """
        Kiểm tra quyền truy cập view
        Args:
            request: HTTP request
            view: View đang xử lý request
        Returns:
            bool: True nếu có quyền, False nếu không
        """
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
    """
    Permission class cho phép chỉ admin truy cập
    """

    def has_permission(self, request, view):
        """
        Kiểm tra quyền truy cập view
        Args:
            request: HTTP request
            view: View đang xử lý request
        Returns:
            bool: True nếu có quyền, False nếu không
        """
        return request.user and request.user.is_staff


class IsPaymentOwnerOrMotelOwner(permissions.BasePermission):
    """
    Permission class cho phép:
    1. Admin truy cập tất cả payment
    2. Người thanh toán (payer) truy cập payment của họ
    3. Chủ nhà truy cập tất cả payment của phòng trong motel của họ
    4. Người thuê phòng truy cập payment của phòng họ đang thuê
    """

    def has_object_permission(self, request, view, obj):
        """
        Kiểm tra quyền truy cập đối tượng payment
        Args:
            request: HTTP request
            view: View đang xử lý request
            obj: Đối tượng payment cần kiểm tra quyền
        Returns:
            bool: True nếu có quyền, False nếu không
        """
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
