from django.contrib import admin
from django.urls import include, path
from rest_framework.routers import DefaultRouter

from . import views

router = DefaultRouter()
# router.register('admins', views.AdminViewSet, basename='admin')
router.register('users', views.UserViewSet, basename='user')
router.register('landlords', views.LandlordViewSet, basename='landlord')
router.register('tenants', views.TenantViewSet, basename='tenant')
router.register('motels', views.MotelViewSet, basename='motel')
router.register('rooms', views.RoomViewSet, basename='room')
router.register('posts', views.PostViewSet, basename='post')
router.register('comments', views.CommentViewSet, basename='comment')
router.register('motelRatings', views.MotelRatingViewSet, basename='motelRating')
router.register('vnpay', views.VNPayViewSet, basename='vnpay')
router.register('searchs', views.SearchViewSet, basename='search')
router.register('search-historys', views.SearchHistoryViewSet, basename='search-history')
router.register('notifications', views.NotificationViewSet, basename='notification')
router.register('chat-rooms', views.ChatRoomViewSet, basename='chat-room')
router.register(r'chat-rooms/(?P<chat_room_id>\d+)/messages', views.MessageViewSet, basename='message')

urlpatterns = [
    # path('', views.index, name="index")
    path('', include(router.urls))
]
