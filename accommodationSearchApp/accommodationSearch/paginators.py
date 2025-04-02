from rest_framework.pagination import LimitOffsetPagination

class ItemPanigator(LimitOffsetPagination):
    default_limit = 3
    max_limit = 50