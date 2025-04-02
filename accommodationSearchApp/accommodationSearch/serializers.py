from rest_framework.serializers import ModelSerializer, SerializerMethodField
from accommodationSearch.models import User, Admin, Landlord, Tenant, Motel, Room, Amenity, RoomTenant, MotelRating, Payment, Notifications, MotelImage, RoomImage, Post, Comment, Favorite, Follow
from rest_framework import serializers



class ItemSerializer(ModelSerializer):
    def to_representation(self, instance):
        data = super().to_representation(instance)
        if hasattr(instance, 'image') and instance.image: 
            data['image'] = instance.image.url
        if hasattr(instance, 'avatar') and instance.avatar:
            data['avatar'] = instance.avatar.url
        return data
    

class UserSerializer(ModelSerializer):
    class Meta:
        model = User
        fields = ['id','username','password', 'first_name', 'last_name', 'role', 'created_date', 'avatar']
        extra_kwargs = {
            'password': {
                'write_only': True
            }
        }
        
    def to_representation(self, instance):
        data = super().to_representation(instance)
        if instance.avtar:
            data['avatar'] = instance.avatar.url
        return data
    
    def create(self, validated_data):
       data = validated_data.copy()
       u = User(**data)
       u.set_password(u.password)
       u.save()
       return u


class AdminSerializer(ItemSerializer):
    class Meta:
        model = Admin
        fields = '__all__'

class LandlordSerializer(ItemSerializer):
    class Meta:
        model = Landlord
        fields = ['user','full_name', 'citizen_id', 'phone', 'avatar', 'address', 'date_of_birth','gender', 'bank_account', 'is_verified']
        

class MotelSerializer(ItemSerializer):
    class Meta:
        model = Motel
        fields = ['id','user', 'motel_name', 'description', 'address', 'district', 'city', 'province', 'longitude', 'latitude', 'total_rooms', 'available_rooms', 'rating_score', 'is_verified']
        
class RoomSerializer(ItemSerializer):
    class Meta:
        model = Room
        fields = ['id', 'motel', 'room_name', 'description', 'area', 'price', 'max_people', 'tenants', 'amenities', 'is_verified']
        
        
