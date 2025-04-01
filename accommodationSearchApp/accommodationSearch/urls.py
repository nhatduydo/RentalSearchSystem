from django.urls import path, include
from . import views
from rest_framework.routers import DefaultRouter

router = DefaultRouter()
router.register('motels', views.MotelViewSet, basename='motel')
router.register('rooms', views.RoomViewSet, basename='room')


urlpatterns = [
     # path('', views.index, name="index")
     path('', include(router.urls))
]

