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
    async def connect(self):
        try:
            # Lấy token từ query string
            query_string = self.scope['query_string'].decode()
            logger.info(f"Received WebSocket connection request with query string: {query_string[:20]}...")

            query_params = parse_qs(query_string)
            token = query_params.get('token', [None])[0]

            if not token:
                logger.error("No token provided in WebSocket connection request")
                await self.close()
                return

            # Loại bỏ prefix "Bearer " nếu có
            if token.startswith('Bearer '):
                token = token[7:]
                logger.info("Removed 'Bearer ' prefix from token")

            logger.info(f"Attempting to validate token: {token[:10]}...")

            # Xác thực token và lấy user
            self.user = await self.get_user_from_token(token)
            if not self.user:
                logger.error("Token validation failed")
                await self.close()
                return

            self.room_id = self.scope['url_route']['kwargs']['room_id']
            logger.info(f"User {self.user.username} attempting to connect to room {self.room_id}")

            self.room_group_name = f'chat_{self.room_id}'

            # Kiểm tra quyền tham gia phòng chat
            if not await self.check_room_permission():
                logger.error(f"User {self.user.username} does not have permission to join room {self.room_id}")
                await self.close()
                return

            # Thêm kênh hiện tại vào group
            await self.channel_layer.group_add(
                self.room_group_name,
                self.channel_name
            )
            logger.info(f"Added user {self.user.username} to room group {self.room_group_name}")

            # Chấp nhận kết nối WebSocket
            await self.accept()
            logger.info(f"WebSocket connection accepted for user {self.user.username} in room {self.room_id}")

        except Exception as e:
            logger.exception(f"Error during WebSocket connection: {str(e)}")
            await self.close()

    @database_sync_to_async
    def get_user_from_token(self, token):
        try:
            logger.info(f"Validating token: {token[:10]}...")

            # Thử xác thực với JWT token trước
            try:
                access_token = AccessToken(token)
                user_id = access_token['user_id']
                logger.info(f"Token is JWT, contains user_id: {user_id}")
                user = User.objects.get(id=user_id)
                logger.info(f"Successfully validated JWT token for user: {user.username}")
                return user
            except Exception as jwt_error:
                logger.info(f"Token is not JWT: {str(jwt_error)}")

                # Nếu không phải JWT, thử xác thực với OAuth2 token
                try:
                    oauth2_token = OAuth2AccessToken.objects.get(token=token)
                    if oauth2_token.is_expired():
                        logger.error("OAuth2 token has expired")
                        return None
                    user = oauth2_token.user
                    logger.info(f"Successfully validated OAuth2 token for user: {user.username}")
                    return user
                except OAuth2AccessToken.DoesNotExist:
                    logger.error("Token not found in OAuth2 tokens")
                    return None
                except Exception as oauth_error:
                    logger.error(f"Error validating OAuth2 token: {str(oauth_error)}")
                    return None

        except Exception as e:
            logger.exception(f"Token validation error: {str(e)}")
            return None

    @database_sync_to_async
    def check_room_permission(self):
        try:
            logger.info(f"Checking room permission for user {self.user.username} in room {self.room_id}")
            chat_room = ChatRoom.objects.get(id=self.room_id, active=True)
            is_participant = self.user in chat_room.participants.all()
            logger.info(f"Room permission check result for user {self.user.username}: {is_participant}")
            return is_participant
        except ChatRoom.DoesNotExist:
            logger.error(f"Chat room {self.room_id} does not exist")
            return False

    async def disconnect(self, close_code):
        try:
            if hasattr(self, 'room_group_name'):
                await self.channel_layer.group_discard(
                    self.room_group_name,
                    self.channel_name
                )
                logger.info(f"User {getattr(self, 'user', 'Unknown')} removed from room group {self.room_group_name}")
            logger.info(f"User {getattr(self, 'user', 'Unknown')} disconnected from room {getattr(self, 'room_id', 'Unknown')} with code {close_code}")
        except Exception as e:
            logger.exception(f"Error during disconnect: {str(e)}")

    async def receive(self, text_data):
        try:
            logger.info(f"Received message from user {self.user.username} in room {self.room_id}")
            text_data_json = json.loads(text_data)
            content = text_data_json['message']
            logger.info(f"Message content: {content[:50]}...")

            # Lưu tin nhắn vào database
            message = await self.save_message(content)
            if not message:
                logger.error("Failed to save message")
                return

            logger.info(f"Message saved successfully with ID: {message.id}")

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
            logger.info(f"Message broadcasted to room {self.room_id}")
        except Exception as e:
            logger.exception(f"Error processing message: {str(e)}")

    @database_sync_to_async
    def save_message(self, content):
        try:
            chat_room = ChatRoom.objects.get(id=self.room_id, active=True)
            if self.user not in chat_room.participants.all():
                logger.error(f"User {self.user.username} is not a participant in room {self.room_id}")
                return None
            message = Message.objects.create(
                chat_room=chat_room,
                sender=self.user,
                content=content
            )
            # Cập nhật updated_date của phòng chat
            chat_room.save()  # Trigger updated_date update
            logger.info(f"Message saved successfully: {message.id}")
            return message
        except ChatRoom.DoesNotExist:
            logger.error(f"Chat room {self.room_id} does not exist")
            return None

    async def chat_message(self, event):
        try:
            logger.info(f"Sending message to WebSocket: {event['message']['id']}")
            await self.send(text_data=json.dumps(event['message']))
        except Exception as e:
            logger.exception(f"Error sending message: {str(e)}")

    async def message_update(self, event):
        try:
            logger.info(f"Processing message update: {event['message']}")
            await self.send(text_data=json.dumps({
                'type': 'message_update',
                'message': event['message']
            }))
        except Exception as e:
            logger.exception(f"Error processing message update: {str(e)}")
