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
User = get_user_model()  # User là model người dùng hiện tại của Django (dùng khi xác thực)


class ChatConsumer(AsyncWebsocketConsumer):
    # Đây là phương thức đặc biệt của AsyncWebsocketConsumer, được gọi khi client bắt đầu kết nối.
    async def connect(self):
        try:
            # Lấy token từ query string
            # Lấy chuỗi query string từ request (ví dụ: ?token=abc123)
            # Parse nó thành dict để lấy giá trị token.
            query_string = self.scope['query_string'].decode()

            query_params = parse_qs(query_string)
            token = query_params.get('token', [None])[0]

            if not token:
                logger.error("Không tìm thấy token trong yêu cầu kết nối WebSocket")
                await self.close()
                return

            # Loại bỏ prefix "Bearer " nếu có
            if token.startswith('Bearer '):
                token = token[7:]

            # Xác thực token và lấy user
            self.user = await self.get_user_from_token(token)  # để kiểm tra token và lấy người dùng.
            if not self.user:
                logger.error("Xác thực token thất bại")
                # Nếu không hợp lệ → đóng kết nối.
                await self.close()
                return

            self.room_id = self.scope['url_route']['kwargs']['room_id']

            self.room_group_name = f'chat_{self.room_id}'

            # Kiểm tra quyền tham gia phòng chat
            if not await self.check_room_permission():
                logger.error(f"Người dùng {self.user.username} không có quyền tham gia phòng {self.room_id}")
                await self.close()
                return

            #  Tham gia vào group WebSocket
            await self.channel_layer.group_add(
                self.room_group_name,
                self.channel_name
            )

            # Chấp nhận kết nối WebSocket
            await self.accept()  # Cho phép kết nối thành công từ client.
            logger.info(f"Người dùng {self.user.username} đã kết nối vào phòng {self.room_id}")

        except Exception as e:
            logger.exception(f"Lỗi trong quá trình kết nối WebSocket: {str(e)}")
            await self.close()

    # Hàm này dùng để xác thực người dùng từ token trong kết nối WebSocket, hỗ trợ cả 2 loại token:
    # JWT (Json Web Token)
    # OAuth2 Access Token
    @database_sync_to_async  # Cho phép hàm đồng bộ (query Django ORM) được dùng trong context async, Vì WebSocket sử dụng async, nên cần chuyển User.objects.get(...) sang async an toàn
    def get_user_from_token(self, token):
        try:
            # Thử xác thực với JWT token trước
            try:
                access_token = AccessToken(token)
                user_id = access_token['user_id']
                user = User.objects.get(id=user_id)
                return user
            except Exception:
                # Nếu không phải JWT, thử xác thực với OAuth2 token
                try:
                    oauth2_token = OAuth2AccessToken.objects.get(token=token)
                    if oauth2_token.is_expired():
                        return None
                    user = oauth2_token.user
                    return user
                except OAuth2AccessToken.DoesNotExist:
                    pass  # Not an OAuth2 token either

            return None
        except Exception as e:
            logger.exception(f"Lỗi xác thực token: {str(e)}")
            return None

    # Kiểm tra người dùng hiện tại (self.user) có quyền tham gia phòng chat (self.room_id) hay không.
    @database_sync_to_async  # Giúp hàm chạy được trong môi trường async của WebSocket. Cho phép gọi các thao tác Django ORM như ChatRoom.objects.get(...)
    def check_room_permission(self):
        try:
            chat_room = ChatRoom.objects.get(id=self.room_id, active=True)
            is_participant = self.user in chat_room.participants.all()
            return is_participant
        except ChatRoom.DoesNotExist:
            logger.error(f"Phòng chat {self.room_id} không tồn tại")
            return False

    async def disconnect(self, close_code):  # hàm bất đồng bộ (async) xử lý khi WebSocket disconnect.
        try:
            if hasattr(self, 'room_group_name'):
                await self.channel_layer.group_discard(
                    self.room_group_name,  # tên nhóm phòng chat
                    self.channel_name  # ID kênh hiện tại (được gán tự động), đại diện cho client đang kết nối.
                )
                # Ghi log việc user nào rời khỏi phòng nào với mã disconnect là gì.
            logger.info(f"Người dùng {getattr(self, 'user', 'Không xác định')} đã ngắt kết nối khỏi phòng {getattr(self, 'room_id', 'Không xác định')} với mã {close_code}")
        except Exception as e:
            logger.exception(f"Lỗi trong quá trình ngắt kết nối: {str(e)}")

    async def receive(self, text_data):
        try:
            text_data_json = json.loads(text_data)
            content = text_data_json['message']

            # Lưu tin nhắn vào database
            message = await self.save_message(content)
            if not message:
                logger.error("Không thể lưu tin nhắn")
                return

            # Gửi tin nhắn đến tất cả trong group
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

    #  lưu tin nhắn mới vào cơ sở dữ liệu trong ứng dụng chat sử dụng Django và asynchronous WebSocket.
    @database_sync_to_async
    def save_message(self, content):
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
            # Cập nhật updated_date của phòng chat
            chat_room.save()  # Trigger updated_date update
            return message
        except ChatRoom.DoesNotExist:
            logger.error(f"Phòng chat {self.room_id} không tồn tại")
            return None

    #  xử lý sự kiện khi nhận tin nhắn từ group WebSocket
    async def chat_message(self, event):
        try:
            await self.send(text_data=json.dumps(event['message']))
        except Exception as e:
            logger.exception(f"Lỗi gửi tin nhắn: {str(e)}")

    async def message_update(self, event):
        try:
            await self.send(text_data=json.dumps({
                'type': 'message_update',
                'message': event['message']
            }))
        except Exception as e:
            logger.exception(f"Lỗi xử lý cập nhật tin nhắn: {str(e)}")
