import os

import django
from accommodationSearch.urls import urlpatterns
from channels.routing import ProtocolTypeRouter, URLRouter
from django.core.asgi import get_asgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'accommodationSearchApp.settings')
django.setup()

# Filter only WebSocket URL patterns
websocket_urlpatterns = [pattern for pattern in urlpatterns if pattern.pattern._route.startswith('ws/')]

application = ProtocolTypeRouter({
    "http": get_asgi_application(),
    "websocket": URLRouter(
        websocket_urlpatterns
    ),
})
