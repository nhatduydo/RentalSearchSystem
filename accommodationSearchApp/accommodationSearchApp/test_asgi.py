import os

import django
from accommodationSearch.routing import websocket_urlpatterns
from channels.routing import ProtocolTypeRouter, URLRouter
from django.core.asgi import get_asgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'accommodationSearchApp.settings')
django.setup()


application = ProtocolTypeRouter({
    "http": get_asgi_application(),
    "websocket": URLRouter(
        websocket_urlpatterns
    ),
})
