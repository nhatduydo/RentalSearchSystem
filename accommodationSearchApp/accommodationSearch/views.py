from django.http import HttpResponse
from .models import Motel, Room, Admin, Landlord, User, Tenant
from rest_framework import viewsets, generics, permissions, parsers
from accommodationSearch import serializers, paginators
from django.shortcuts import get_object_or_404
from rest_framework.response import Response
from unidecode import unidecode
from django.contrib.auth import authenticate
from rest_framework.decorators import action
def index(request):
    return HttpResponse("HỆ THỐNG HỖ TRỢ TÌM KIẾM NHÀ TRỌ")

class AdminViewSet(viewsets.ViewSet, generics.ListAPIView):
    queryset = Admin.objects.filter(active = True)
    serializer_class = serializers.AdminSerializer

    
    

class UserViewSet(viewsets.ViewSet,
                  generics.ListAPIView,
                  generics.RetrieveAPIView,
                  generics.CreateAPIView,
                  generics.UpdateAPIView,
                  generics.DestroyAPIView):
    queryset = User.objects.filter(is_active=True)
    serializer_class = serializers.UserSerializer
    pagination_class = paginators.ItemPanigator
    arser_classes = [parsers.MultiPartParser, ]

    def get_permissions(self):
        if self.action in ['create', 'login']:
            return [permissions.AllowAny()]
        return [permissions.IsAuthenticated()]
    
    def create(self, request, *args, **kwargs):
        role = request.data.get('role')
        if role == "LANDLORD":
            landlord_serializer = serializers.LandlordSerializer(data=request.data)
            if landlord_serializer.is_valid():
                landlord_serializer.save()
            else:
                return Response(landlord_serializer.errors, status=400)
        elif role == "TENANT":
            tenant_serializer = serializers.TenantSerializer(data=request.data)
            if tenant_serializer.is_valid():
                tenant_serializer.save()
            else:
                return Response(tenant_serializer.errors, status=400)
        else:
            return Response({"error": "Invalid role"}, status=400)

        return super().create(request, *args, **kwargs)
    
    @action(methods=['GET', 'PATCH'], url_path = 'current-user', detail=False, permission_classes=[permissions.IsAuthenticated])
    def get_Current_user(self, request):
        if request.method.__eq__("PATCH"):
            user = request.user
            for key, value in request.data.items():
                if key in ['first_name', 'last_name']:
                    setattr(user, key, value)
                elif key == 'password':
                    user.set_password(value)
            user.save()

            return Response(serializers.UserSerializer(user).data)
        return Response(serializers.UserSerializer(request.user).data)
            
    @action(methods=['POST'], url_path='login', detail=False, permission_classes=[permissions.AllowAny])
    def login(self, request):
        username = request.data.get("username")
        password = request.data.get("password")
        user = authenticate(username=username, password=password)
        
        if user is not None:
            if user.is_active:
                return Response(self.serializer_class(user).data)
            else:
                return Response({"error": "user is inactive"}, status=403)
        return Response({"error": "Thông tin đăng nhập không hợp lệ"}, status=401)
    
    @action(methods=['PATCH'], url_path='change-password', detail=False, permission_classes=[permissions.IsAuthenticated])
    def change_password(self, request):
        old_password = request.data.get("old_password")
        new_password = request.data.get("new_password")
        confirm_password = request.data.get("confirm_password")
        
        if not request.user.check_password(old_password):
            return Response({"error": "Mật khẩu cũ không chính xác"}, status=400)
        
        if new_password != confirm_password:
            return Response({"error", "Mật khẩu mới không khớp"}, status=400)
        
        request.user.set_password(new_password)
        request.user.save()
        return Response({"success": "Thay đổi mật khẩu thành công"})
    
    def retrieve(self, request, pk=None):
        if pk.isdigit():
            username = get_object_or_404(User, id = pk)
        else: 
            username = get_object_or_404(User, slug = pk)
            
        serializers = self.get_serializer(username)
        return Response(serializers.data)
        


class MotelViewSet(viewsets.ViewSet, generics.ListCreateAPIView , generics.RetrieveUpdateDestroyAPIView):
    queryset =  Motel.objects.filter(active = True)
    serializer_class = serializers.MotelSerializer
    pagination_class = paginators.ItemPanigator
    
    def retrieve(self, request, pk=None):
        if pk.isdigit():
            motel = get_object_or_404(Motel, id = pk)
        else: 
            motel = get_object_or_404(Motel, slug = pk)
            
        serializers = self.get_serializer(motel)
        return Response(serializers.data)
    
    
    
class RoomViewSet(viewsets.ViewSet, generics.ListCreateAPIView, generics.RetrieveUpdateDestroyAPIView):
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
    

