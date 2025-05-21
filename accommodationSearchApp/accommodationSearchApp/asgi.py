import os

import django
from channels.routing import ProtocolTypeRouter, URLRouter
from django.core.asgi import get_asgi_application

# Set Django settings module before any Django imports
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'accommodationSearchApp.settings')


django.setup()


def get_websocket_urlpatterns():
    from accommodationSearch.urls import urlpatterns
    return [pattern for pattern in urlpatterns if pattern.pattern.regex.pattern.startswith('ws/')]


application = ProtocolTypeRouter({
    "http": get_asgi_application(),
    "websocket": URLRouter(
        get_websocket_urlpatterns()
    ),
})
