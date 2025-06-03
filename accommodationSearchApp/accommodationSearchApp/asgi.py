import os

import django
from accommodationSearch.middleware.token_auth_middleware import \
    TokenAuthMiddleware
from channels.routing import ProtocolTypeRouter, URLRouter
from django.core.asgi import get_asgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'accommodationSearchApp.settings')

django.setup()

def get_websocket_urlpatterns():
    from accommodationSearch.urls import urlpatterns
    return [pattern for pattern in urlpatterns if pattern.pattern.regex.pattern.startswith('ws/')]

application = ProtocolTypeRouter({
    "http": get_asgi_application(),
    "websocket": TokenAuthMiddleware(
        URLRouter(
            get_websocket_urlpatterns()
        )
    ),
})
