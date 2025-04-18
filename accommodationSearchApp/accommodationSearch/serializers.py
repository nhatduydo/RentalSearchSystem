from rest_framework.serializers import ModelSerializer, SerializerMethodField
from accommodationSearch.models import User, LikeComment, Admin, Landlord, Tenant, Motel, Room, Amenity, RoomTenant, MotelRating, Payment, Notifications, MotelImage, RoomImage, Post, Comment, Favorite, Follow
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
        if instance.avatar:
            data['avatar'] = instance.avatar.url
        return data
    
    def create(self, validated_data):
        password = validated_data.pop('password')
        user = User(**validated_data) 
        user.set_password(password) 
        user.save()
        return user
    
    def update(self, instance, validated_data):
        password = validated_data.pop('password', None) 
        for attr, value in validated_data.items():
            setattr(instance, attr, value)              

        if password:
            instance.set_password(password)          

        instance.save()
        return instance


# class AdminSerializer(ItemSerializer):
#     class Meta:
#         model = Admin
#         fields = '__all__'

class LandlordSerializer(ItemSerializer):
    class Meta:
        model = Landlord
        fields = ['user','full_name', 'citizen_id', 'phone', 'avatar', 'address', 'date_of_birth','gender', 'bank_account', 'is_verified']
        

class TenantSerializer(ItemSerializer):
    class Meta:
        model = Tenant
        fields = ['user', 'full_name', 'citizen_id', 'phone', 'avatar', 'address', 'date_of_birth','gender', 'bank_account', 'rooms']

class MotelSerializer(ItemSerializer):
    class Meta:
        model = Motel
        fields = ['id','user', 'motel_name', 'description', 'address', 'district', 'city', 'province', 'longitude', 'latitude', 'total_rooms', 'available_rooms', 'rating_score', 'is_verified']
        
class RoomSerializer(ItemSerializer):
    class Meta:
        model = Room
        fields = ['id', 'motel', 'room_name', 'description', 'area', 'price', 'max_people', 'tenants', 'amenities', 'is_verified']
        
        
class CommentSerializer(ItemSerializer):
    def to_representation(self, instance):
        data = super().to_representation(instance)
        data['user'] = UserSerializer(instance.user).data
        return data
    
    def get_replies(self, comment):
        child_comments = comment.replies.filter(active=True)
        return CommentSerializer(child_comments, many=True, context=self.context).data
    
    def get_liked(self, comment):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return LikeComment.object.filter(comment=comment, user=request.user, active=True).exists()
    
    def to_representation(self, instance):
        data = super().to_representation(instance)
        data['user'] = UserSerializer(instance.user).data
        data['like'] = self.get_liked(instance)
        data['replies'] = self.get_replies(instance)
        return data
    
    class Meta:
        model = Comment
        fields = ['id', 'post', 'user', 'content', 'parent', 'created_date', 'replies']
        extra_kwargs = {
            'post': {'write_only': True},
            'parent': {'write_only': True}
        }
    
    