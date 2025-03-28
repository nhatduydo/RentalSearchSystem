from rest_framework.serializers import ModelSerializer, SerializerMethodField
from accommodationSearch.models import User, Admin, Landlord, Tenant, Motel, Room, Amenity, RoomTenant, MotelRating, Payment, Notifications, MotelImage, RoomImage, Post, Comment, Favorite, Follow


class ItemSerializer(ModelSerializer):
    def to_representation(self, instance):
        data = super().to_representation(instance)
        if instance.image: 
            data['image'] = instance.image.url
        if instance.avatar:
            data['avatar'] = instance.avatar.url
        return data
    
class LandlordSerializer(ItemSerializer):
    class Meta:
        model = Landlord
        fields = ['id', 'user_id', 'is_verified', 'full_name', 'citizen_id', 'phone', 'avatar', 'address', 'date_of_birth', 'bank_account', 'gender']