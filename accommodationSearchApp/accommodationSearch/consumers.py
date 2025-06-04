import json
import logging
from urllib.parse import parse_qs

from channels.db import database_sync_to_async
from channels.generic.websocket import AsyncWebsocketConsumer
from django.contrib.auth import get_user_model
from django.core.exceptions import PermissionDenied
from oauth2_provider.models import AccessToken as OAuth2AccessToken
from rest_framework_simplejwt.tokens import AccessToken

from .models import ChatRoom, Message

logger = logging.getLogger(__name__)
User = get_user_model()


class ChatConsumer(AsyncWebsocketConsumer):
    """
    Consumer xử lý các kết nối WebSocket cho chat
    Kế thừa từ AsyncWebsocketConsumer để xử lý bất đồng bộ
    """

    async def connect(self):
        """
        Xử lý khi client kết nối đến WebSocket
        - Kiểm tra token xác thực
        - Kiểm tra quyền truy cập phòng chat
        - Thêm client vào group chat
        """
        try:
            # Lấy và decode query string từ URL
            query_string = self.scope['query_string'].decode()
            # Parse query string thành dictionary
            query_params = parse_qs(query_string)
            # Lấy token từ query params
            token = query_params.get('token', [None])[0]

            # Kiểm tra nếu không có token
            if not token:
                logger.error("Không tìm thấy token trong yêu cầu kết nối WebSocket")
                await self.close()
                return

            # Xử lý token nếu có prefix "Bearer "
            if token.startswith('Bearer '):
                token = token[7:]

            # Xác thực token và lấy thông tin user
            self.user = await self.get_user_from_token(token)
            if not self.user:
                logger.error("Xác thực token thất bại")
                await self.close()
                return

            # Lấy room_id từ URL parameters
            self.room_id = self.scope['url_route']['kwargs']['room_id']
            # Tạo tên group cho phòng chat
            self.room_group_name = f'chat_{self.room_id}'

            # Kiểm tra quyền truy cập phòng chat
            if not await self.check_room_permission():
                logger.error(f"Người dùng {self.user.username} không có quyền tham gia phòng {self.room_id}")
                await self.close()
                return

            # Thêm client vào group chat
            await self.channel_layer.group_add(
                self.room_group_name,
                self.channel_name
            )

            # Chấp nhận kết nối WebSocket
            await self.accept()
            logger.info(f"Người dùng {self.user.username} đã kết nối vào phòng {self.room_id}")

        except Exception as e:
            logger.exception(f"Lỗi trong quá trình kết nối WebSocket: {str(e)}")
            await self.close()

    @database_sync_to_async
    def get_user_from_token(self, token):
        """
        Xác thực token và lấy thông tin user
        Hỗ trợ cả JWT token và OAuth2 token
        """
        try:
            # Thử xác thực với JWT token
            try:
                access_token = AccessToken(token)
                user_id = access_token['user_id']
                user = User.objects.get(id=user_id)
                return user
            except Exception:
                # Nếu JWT không hợp lệ, thử với OAuth2 token
                try:
                    oauth2_token = OAuth2AccessToken.objects.get(token=token)
                    if oauth2_token.is_expired():
                        return None
                    user = oauth2_token.user
                    return user
                except OAuth2AccessToken.DoesNotExist:
                    pass

            return None
        except Exception as e:
            logger.exception(f"Lỗi xác thực token: {str(e)}")
            return None

    @database_sync_to_async
    def check_room_permission(self):
        """
        Kiểm tra quyền truy cập phòng chat
        - Kiểm tra phòng chat có tồn tại và active
        - Kiểm tra user có phải là thành viên của phòng
        """
        try:
            chat_room = ChatRoom.objects.get(id=self.room_id, active=True)
            is_participant = self.user in chat_room.participants.all()
            return is_participant
        except ChatRoom.DoesNotExist:
            logger.error(f"Phòng chat {self.room_id} không tồn tại")
            return False

    async def disconnect(self, close_code):
        """
        Xử lý khi client ngắt kết nối
        - Xóa client khỏi group chat
        - Ghi log thông tin ngắt kết nối
        """
        try:
            if hasattr(self, 'room_group_name'):
                await self.channel_layer.group_discard(
                    self.room_group_name,
                    self.channel_name  # ID kênh hiện tại (được gán tự động), đại diện cho client đang kết nối.
                )
                # Ghi log việc user nào rời khỏi phòng nào với mã disconnect là gì.
            logger.info(f"Người dùng {getattr(self, 'user', 'Không xác định')} đã ngắt kết nối khỏi phòng {getattr(self, 'room_id', 'Không xác định')} với mã {close_code}")
        except Exception as e:
            logger.exception(f"Lỗi trong quá trình ngắt kết nối: {str(e)}")

    async def receive(self, text_data):
        """
        Xử lý khi nhận tin nhắn từ client
        - Parse dữ liệu JSON
        - Lưu tin nhắn vào database
        - Gửi tin nhắn đến tất cả client trong phòng
        """
        try:
            text_data_json = json.loads(text_data)
            content = text_data_json['message']

            # Lưu tin nhắn vào database
            message = await self.save_message(content)
            if not message:
                logger.error("Không thể lưu tin nhắn")
                return

            # Gửi tin nhắn đến tất cả client trong phòng
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'chat_message',
                    'message': {
                        'id': message.id,
                        'content': message.content,
                        'sender_id': message.sender.id,
                        'sender_name': message.sender.username,
                        'created_date': message.created_date.isoformat(),
                        'is_read': message.is_read
                    }
                }
            )
        except Exception as e:
            logger.exception(f"Lỗi xử lý tin nhắn: {str(e)}")

    @database_sync_to_async
    def save_message(self, content):
        """
        Lưu tin nhắn mới vào database
        - Kiểm tra phòng chat tồn tại
        - Kiểm tra quyền gửi tin nhắn
        - Tạo và lưu tin nhắn mới
        """
        try:
            chat_room = ChatRoom.objects.get(id=self.room_id, active=True)
            if self.user not in chat_room.participants.all():
                logger.error(f"Người dùng {self.user.username} không phải là thành viên của phòng {self.room_id}")
                return None
            message = Message.objects.create(
                chat_room=chat_room,
                sender=self.user,
                content=content
            )
            chat_room.save()
            return message
        except ChatRoom.DoesNotExist:
            logger.error(f"Phòng chat {self.room_id} không tồn tại")
            return None

    async def chat_message(self, event):
        """
        Xử lý sự kiện khi nhận tin nhắn từ group
        - Gửi tin nhắn đến client
        """
        try:
            await self.send(text_data=json.dumps(event['message']))
        except Exception as e:
            logger.exception(f"Lỗi gửi tin nhắn: {str(e)}")

    async def message_update(self, event):
        """
        Xử lý sự kiện cập nhật tin nhắn
        - Gửi thông tin cập nhật đến client
        """
        try:
            await self.send(text_data=json.dumps({
                'type': 'message_update',
                'message': event['message']
            }))
        except Exception as e:
            logger.exception(f"Lỗi xử lý cập nhật tin nhắn: {str(e)}")
