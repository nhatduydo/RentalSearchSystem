import json

from channels.generic.websocket import AsyncWebsocketConsumer


class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.room_id = self.scope['url_route']['kwargs']['room_id']
        self.room_group_name = f'chat_{self.room_id}'

        # Thêm kênh hiện tại vào group
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )

        # Chấp nhận kết nối WebSocket
        await self.accept()

    async def disconnect(self, close_code):
        # Xóa kênh khỏi group khi ngắt kết nối
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )

    async def receive(self, text_data):
        # Xử lý tin nhắn nhận được
        text_data_json = json.loads(text_data)
        message = text_data_json['message']
        sender_id = text_data_json['sender_id']

        # Gửi tin nhắn đến tất cả trong group
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'chat_message',
                'message': message,
                'sender_id': sender_id
            }
        )

    async def chat_message(self, event):
        # Gửi tin nhắn đến WebSocket
        message = event['message']
        sender_id = event['sender_id']

        await self.send(text_data=json.dumps({
            'message': message,
            'sender_id': sender_id
        }))
