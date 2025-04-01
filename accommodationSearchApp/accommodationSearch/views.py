from django.http import HttpResponse
from django.shortcuts import redirect, render
import cloudinary.uploader
from .models import Motel, Room, MotelImage
from rest_framework import viewsets, generics
from accommodationSearch import serializers

def index(request):
    return HttpResponse("HỆ THỐNG HỖ TRỢ TÌM KIẾM NHÀ TRỌ")

class MotelViewSet(viewsets.ViewSet, generics.ListAPIView):
    queryset = Motel.objects.filter(active = True)
    serializer_class = serializers.MotelSerializer
    
class RoomViewSet(viewsets.ViewSet, generics.ListAPIView):
    queryset = Room.objects.filter(active = True)
    serializer_class = serializers.RoomSerializer