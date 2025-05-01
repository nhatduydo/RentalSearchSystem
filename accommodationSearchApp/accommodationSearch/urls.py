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

urlpatterns = [
    # path('', views.index, name="index")
    path('', include(router.urls)),
    # VNPay API endpoints
    path('payment/create/', views.create_payment, name='create-payment'),
    path('payment/return/', views.payment_return, name='payment-return'),
]
