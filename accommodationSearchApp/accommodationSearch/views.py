from django.http import HttpResponse
from .models import Motel, Room, Admin, Landlord, User, Tenant
from rest_framework import viewsets, generics, permissions
from accommodationSearch import serializers, paginators
from django.shortcuts import get_object_or_404
from rest_framework.response import Response
from unidecode import unidecode

def index(request):
    return HttpResponse("HỆ THỐNG HỖ TRỢ TÌM KIẾM NHÀ TRỌ")

class AdminViewSet(viewsets.ViewSet, generics.ListAPIView):
    queryset = Admin.objects.filter(active = True)
    serializer_class = serializers.AdminSerializer

class UserViewSet(viewsets.ViewSet, generics.ListAPIView):
    queryset = User.objects.all()
    serializer_class = serializers.UserSerializer
    pagination_class = paginators.ItemPanigator
    
    def get_permissions(self):
        if self.action in ['create', 'login']:
            return [permissions.AllowAny()]
        return [permissions.IsAuthenticated()]


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

    def retrieve(self, request, pk=None):
        if pk.isdigit():
            room = get_object_or_404(Room, id = pk)
        else: 
            room = get_object_or_404(Room, slug = pk)
            
        serializers = self.get_serializer(room)
        return Response(serializers.data)
    
    def get_queryset(self):
        query = self.queryset
        
        if self.action.__eq__('list'):
            search_query  = self.request.query_params.get('q')
            if search_query :
                query = query.filter(room_name__icontains = search_query)
                
            motel_id = self.request.query_params.get('motel_id')
            if motel_id:
                query = query.filter(motel_id = motel_id)
                
            motel_slug = self.request.query_params.get('motel_slug')
            if motel_slug:
                motel = get_object_or_404(Motel, slug=motel_slug)
                query = query.filter(motel = motel)
        return query
 
    
class LandlordViewSet(viewsets.ViewSet, generics.ListAPIView):
    queryset = Landlord.objects.filter(active = True)
    serializer_class = serializers.LandlordSerializer
    pagination_class = paginators.ItemPanigator

    def retrieve(self, request, pk=None):
        if pk.isdigit():
            landlord = get_object_or_404(Landlord, user_id = pk)
        else: 
            landlord = get_object_or_404(Landlord, slug = pk)
            
        serializers = self.get_serializer(landlord)
        return Response(serializers.data)
    
    def get_queryset(self):
        query = self.queryset
        
        if self.action.__eq__('list'):
            
            user_id = self.request.query_params.get('id')
            if user_id:
                query = query.filter(user_id = user_id)
            
            search_query  = self.request.query_params.get('q')
            if search_query :
                query = query.filter(full_name__icontains=search_query)
                
            slug_source = self.request.query_params.get('slug_source')
            if slug_source:
                query = query.filter(slug = slug_source)
        return query
    
    
class TenantViewSet(viewsets.ViewSet, generics.ListAPIView):
    queryset = Tenant.objects.filter(active = True)
    serializer_class = serializers.TenantSerializer
    pagination_class = paginators.ItemPanigator
    
    def retrieve(self, request, pk=None):
        if pk.isdigit():
            tenant = get_object_or_404(Tenant, user_id = pk)
        else: 
            tenant = get_object_or_404(Tenant, slug = pk)
            
        serializers = self.get_serializer(tenant)
        return Response(serializers.data)
    
    def get_queryset(self):
        query = self.queryset
        
        if self.action.__eq__('list'):
            
            user_id = self.request.query_params.get('id')
            if user_id:
                query = query.filter(user_id = user_id)
            
            search_query  = self.request.query_params.get('q')
            if search_query :
                query = query.filter(full_name__icontains=search_query)
                
            slug_source = self.request.query_params.get('slug_source')
            if slug_source:
                query = query.filter(slug = slug_source)
        return query