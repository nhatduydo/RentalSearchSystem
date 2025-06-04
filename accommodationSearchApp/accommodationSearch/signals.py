from accommodationSearch.models import Motel, MotelImage, Room, RoomImage
from django.db.models.signals import post_delete, post_save
# Import decorator receiver để đăng ký signal handlers
from django.dispatch import receiver


# Đăng ký signal handler cho RoomImage
# post_save: Kích hoạt sau khi lưu RoomImage
# post_delete: Kích hoạt sau khi xóa RoomImage
@receiver([post_save, post_delete], sender=RoomImage)
def update_room_verification(sender, instance, **kwargs):
    """
    Cập nhật trạng thái xác thực của phòng khi có thay đổi về hình ảnh

    Args:
        sender: Model gửi signal (RoomImage)
        instance: Instance của RoomImage vừa được lưu/xóa
        **kwargs: Các tham số bổ sung từ signal
    """
    # Lấy phòng liên kết với hình ảnh
    room = instance.room
    # In thông tin debug
    print(f"Instance room: {instance.room}")
    # Kiểm tra và cập nhật trạng thái xác thực của phòng
    room.check_verification()
