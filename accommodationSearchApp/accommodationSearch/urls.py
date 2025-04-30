from django.urls import path, include
from . import views
from rest_framework.routers import DefaultRouter

router = DefaultRouter()
# router.register('admins', views.AdminViewSet, basename='admin')
router.register('users', views.UserViewSet, basename='user')
router.register('landlords', views.LandlordViewSet, basename='landlord')
router.register('tenants', views.TenantViewSet, basename='tenant')
router.register('motels', views.MotelViewSet, basename='motel')
router.register('rooms', views.RoomViewSet, basename='room')
router.register('posts', views.PostViewSet, basename='post')
router.register('comments', views.CommentViewSet, basename='comment')

urlpatterns = [
     # path('', views.index, name="index")
     path('', include(router.urls)),
]

