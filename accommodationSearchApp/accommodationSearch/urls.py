# from allauth.socialaccount.models import SocialAccount, SocialApp, SocialToken
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
router.register('payments', views.PaymentViewSet, basename='payment')
router.register('searchs', views.SearchViewSet, basename='search')
router.register('search-histories', views.SearchHistoryViewSet, basename='search-history')
router.register('notifications', views.NotificationViewSet, basename='notification')
router.register('chat-rooms', views.ChatRoomViewSet, basename='chat-room')
router.register(r'chat-rooms/(?P<chat_room_id>\d+)/messages', views.MessageViewSet, basename='message')
router.register('follows', views.FollowViewSet, basename='follows')
router.register('room-tenants', views.RoomTenantViewSet, basename='room-tenant')
router.register('motel-images', views.MotelImageViewSet, basename='motel-image')
router.register('room-images', views.RoomImageViewSet, basename='room-image')
router.register('amenities', views.AmenityViewSet, basename='amenity')
router.register('favorites', views.FavoriteViewSet, basename='favorite')
router.register('statistics', views.StatisticsViewSet, basename='statistics')

urlpatterns = [
    path('', include(router.urls)),
    # path('google-auth/', views.GoogleAuthView.as_view(), name='google-auth'),
]
