from urllib.parse import parse_qs

from channels.db import database_sync_to_async
from django.contrib.auth import get_user_model
from django.contrib.auth.models import AnonymousUser
from oauth2_provider.models import AccessToken as OAuth2AccessToken
from rest_framework.authtoken.models import Token
from rest_framework_simplejwt.tokens import AccessToken

User = get_user_model()


@database_sync_to_async
def get_user(token_key):
    try:
        # Thử xác thực với JWT token
        try:
            access_token = AccessToken(token_key)
            user_id = access_token['user_id']
            return User.objects.get(id=user_id)
        except Exception:
            # Nếu không phải JWT, thử xác thực với OAuth2 token
            try:
                oauth2_token = OAuth2AccessToken.objects.get(token=token_key)
                if not oauth2_token.is_expired():
                    return oauth2_token.user
            except OAuth2AccessToken.DoesNotExist:
                pass

        # Cuối cùng thử với Token model
        try:
            token = Token.objects.get(key=token_key)
            return token.user
        except Token.DoesNotExist:
            return AnonymousUser()
    except Exception:
        return AnonymousUser()


class TokenAuthMiddleware:
    def __init__(self, inner):
        self.inner = inner

    def __call__(self, scope):
        return TokenAuthMiddlewareInstance(scope, self.inner)


class TokenAuthMiddlewareInstance:
    def __init__(self, scope, inner):
        self.scope = dict(scope)
        self.inner = inner

    async def __call__(self, receive, send):
        query_string = self.scope['query_string'].decode()
        token_key = parse_qs(query_string).get('token', [None])[0]

        # Loại bỏ prefix "Bearer " nếu có
        if token_key and token_key.startswith('Bearer '):
            token_key = token_key[7:]

        self.scope['user'] = await get_user(token_key)
        inner = self.inner(self.scope)
        return await inner(receive, send)
