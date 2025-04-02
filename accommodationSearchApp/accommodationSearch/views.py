from django.http import HttpResponse
from django.shortcuts import redirect, render
import cloudinary.uploader
from .models import Motel, Room, MotelImage, Admin, Landlord
from rest_framework import viewsets, generics
from accommodationSearch import serializers, paginators

def index(request):
    return HttpResponse("HỆ THỐNG HỖ TRỢ TÌM KIẾM NHÀ TRỌ")

class AdminViewSet(viewsets.ViewSet, generics.ListAPIView):
    queryset = Admin.objects.filter(active = True)
    serializer_class = serializers.AdminSerializer
    

class MotelViewSet(viewsets.ViewSet, generics.ListAPIView):
    queryset = Motel.objects.filter(active = True)
    serializer_class = serializers.MotelSerializer
    pagination_class = paginators.ItemPanigator
    
class RoomViewSet(viewsets.ViewSet, generics.ListAPIView):
    queryset = Room.objects.filter(active = True)
    serializer_class = serializers.RoomSerializer
    pagination_class = paginators.ItemPanigator

    def get_queryset(self):
        query = self.queryset
        
        if self.action.__eq__('list'):
            q = self.request.query_params.get('q')
            if q:
                query = query.filter(subject__icontains = q)
                
            motel_id = self.request.query_params.get('motel_id')
            if motel_id:
                query = query.filter(motel_Id = motel_id)
        return query
    
class LandlordViewSet(viewsets.ViewSet, generics.ListAPIView):
    queryset = Landlord.objects.filter(active = True)
    serializer_class = serializers.LandlordSerializer
    pagination_class = paginators.ItemPanigator
