from django.http import HttpResponse
from .models import Motel, Room, Admin, Landlord
from rest_framework import viewsets, generics
from accommodationSearch import serializers, paginators
from django.shortcuts import get_object_or_404
from rest_framework.response import Response


def index(request):
    return HttpResponse("HỆ THỐNG HỖ TRỢ TÌM KIẾM NHÀ TRỌ")

class AdminViewSet(viewsets.ViewSet, generics.ListAPIView):
    queryset = Admin.objects.filter(active = True)
    serializer_class = serializers.AdminSerializer
    

class MotelViewSet(viewsets.ViewSet, generics.ListAPIView):
    queryset = Motel.objects.filter(active = True)
    serializer_class = serializers.MotelSerializer
    pagination_class = paginators.ItemPanigator
    
    
    def retrieve(self, request, pk=None):
        if pk.isdigit():
            motel = get_object_or_404(Motel, id = pk)
        else: 
            motel = get_object_or_404(Motel, slug = pk)
            
        serializers = self.get_serializer(motel)
        return Response(serializers.data)
    
    
class RoomViewSet(viewsets.ViewSet, generics.ListAPIView):
    queryset = Room.objects.filter(active = True)
    serializer_class = serializers.RoomSerializer
    pagination_class = paginators.ItemPanigator

    def get_queryset(self):
        query = self.queryset
        
        if self.action.__eq__('list'):
            q = self.request.query_params.get('q')
            if q:
                query = query.filter(room_name__icontains = q)
                
            motel_id = self.request.query_params.get('motel_id')
            if motel_id:
                query = query.filter(motel_id = motel_id)
        return query
    
class LandlordViewSet(viewsets.ViewSet, generics.ListAPIView):
    queryset = Landlord.objects.filter(active = True)
    serializer_class = serializers.LandlordSerializer
    pagination_class = paginators.ItemPanigator
