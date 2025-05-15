import logging

from channels.generic.websocket import AsyncWebsocketConsumer

logger = logging.getLogger(__name__)


class TestConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        logger.info("WebSocket connection attempt")
        try:
            await self.accept()
            logger.info("WebSocket connection accepted")
        except Exception as e:
            logger.error(f"Error accepting WebSocket connection: {e}")
            raise

    async def disconnect(self, close_code):
        logger.info(f"WebSocket disconnected with code: {close_code}")

    async def receive(self, text_data):
        logger.info(f"Received message: {text_data}")
        try:
            await self.send(text_data=text_data)
            logger.info("Message sent successfully")
        except Exception as e:
            logger.error(f"Error sending message: {e}")
            raise
