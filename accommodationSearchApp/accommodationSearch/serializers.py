from accommodationSearch.models import (Admin, Amenity, ChatRoom, Comment,
                                        Favorite, Follow, Landlord,
                                        LikeComment, LikeMotel, Message, Motel,
                                        MotelImage, MotelRating, Notifications,
                                        NotificationType, Payment, Post,
                                        PostImage, Room, RoomImage, RoomTenant,
                                        RoomTenantStatus, SearchHistory,
                                        Tenant, User)
from rest_framework import serializers
from rest_framework.serializers import ModelSerializer


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
        fields = ['id', 'username', 'password', 'email', 'first_name', 'last_name', 'role', 'created_date', 'avatar']
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
        fields = ['user', 'full_name', 'citizen_id', 'phone', 'address', 'date_of_birth', 'gender', 'bank_account', 'is_verified']
        read_only_fields = ['is_verified']


class TenantSerializer(ItemSerializer):
    class Meta:
        model = Tenant
        fields = ['user', 'full_name', 'citizen_id', 'phone', 'address', 'date_of_birth', 'gender', 'bank_account', 'rooms']

    def to_representation(self, instance):
        data = super().to_representation(instance)
        # Loại bỏ các giá trị trùng lặp trong rooms
        if 'rooms' in data:
            data['rooms'] = list(set(data['rooms']))
        return data


class MotelSerializer(ItemSerializer):
    def get_liked(self, motel):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return LikeMotel.objects.filter(motel=motel, user=request.user, active=True).exists()

    def to_representation(self, instance):
        data = super().to_representation(instance)
        data['user'] = UserSerializer(instance.user).data
        data['like'] = self.get_liked(instance)
        return data

    class Meta:
        model = Motel
        fields = ['id', 'user', 'motel_name', 'description', 'address', 'district', 'city', 'province', 'longitude', 'latitude', 'total_rooms', 'available_rooms', 'rating_score', 'is_verified']
        read_only_fields = ['user', 'rating_score', 'is_verified']


class MotelRatingSerializer(ItemSerializer):
    class Meta:
        model = MotelRating
        fields = ['id', 'motel', 'user', 'rating', 'comment', 'created_date']
        read_only_fields = ['id', 'created_date']

    def validate_rating(self, value):
        if value < 1 or value > 5:
            raise serializers.ValidationError("Rating must be between 1 and 5")
        return value

    def to_representation(self, instance):
        data = super().to_representation(instance)
        data['user'] = UserSerializer(instance.user).data
        data['motel'] = MotelSerializer(instance.motel).data
        return data


class RoomSerializer(ItemSerializer):
    amenities = serializers.PrimaryKeyRelatedField(many=True, queryset=Amenity.objects.all())
    amenities_display = serializers.SerializerMethodField()

    class Meta:
        model = Room
        fields = [
            'id', 'motel', 'room_name', 'description', 'area', 'price', 'max_people',
            'tenants', 'amenities', 'amenities_display', 'is_verified'
        ]

    def get_amenities_display(self, obj):
        return AmenitySerializer(obj.amenities.all(), many=True).data

    def to_representation(self, instance):
        data = super().to_representation(instance)
        # Loại bỏ các giá trị trùng lặp trong tenants
        if 'tenants' in data:
            data['tenants'] = list(set(data['tenants']))
        return data


class RoomTenantSerializer(ItemSerializer):
    class Meta:
        model = RoomTenant
        fields = ['id', 'room', 'tenant', 'start_date', 'end_date', 'status',
                  'is_paid', 'created_date', 'updated_date']
        read_only_fields = ['tenant', 'status', 'is_paid', 'created_date',
                            'updated_date']

    def to_representation(self, instance):
        data = super().to_representation(instance)
        data['room'] = RoomSerializer(instance.room).data
        data['tenant'] = TenantSerializer(instance.tenant).data
        return data

    def validate(self, data):
        if data.get('start_date') and data.get('end_date'):
            if data['start_date'] > data['end_date']:
                raise serializers.ValidationError("Ngày bắt đầu phải trước ngày kết thúc")
        return data

    def validate_status(self, value):
        if value not in dict(RoomTenantStatus.choices):
            raise serializers.ValidationError("Trạng thái không hợp lệ")
        return value


class PostImageSerializer(ItemSerializer):
    class Meta:
        model = PostImage
        fields = ['id', 'image_url', 'image_type', 'order']

    def to_representation(self, instance):
        data = super().to_representation(instance)
        if instance.image_url:
            data['image_url'] = instance.image_url.url
        return data


class PostSerializer(ItemSerializer):
    user = UserSerializer(read_only=True)
    comments_count = serializers.SerializerMethodField()
    images = PostImageSerializer(many=True, read_only=True)

    class Meta:
        model = Post
        fields = ['id', 'user', 'post_type', 'title', 'content', 'created_date',
                  'min_price', 'max_price', 'comments_count', 'images']

    def get_comments_count(self, obj):
        return Comment.objects.filter(post=obj).count()


class PostDetailSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    comments = serializers.SerializerMethodField()
    comments_count = serializers.SerializerMethodField()
    images = PostImageSerializer(many=True, read_only=True)

    class Meta:
        model = Post
        fields = [
            'id', 'user', 'post_type', 'title', 'content', 'created_date',
            'desired_address', 'min_price', 'max_price', 'radius_km',
            'desired_latitude', 'desired_longitude', 'motel', 'comments',
            'comments_count', 'images'
        ]

    def get_comments(self, obj):
        comments = Comment.objects.filter(post=obj, parent=None)
        return CommentSerializer(comments, many=True, context=self.context).data

    def get_comments_count(self, obj):
        return Comment.objects.filter(post=obj).count()

    def create(self, validated_data):
        request = self.context.get('request')
        images_data = request.FILES.getlist('images')

        post = super().create(validated_data)

        # Lưu các hình ảnh
        if images_data:
            for order, image in enumerate(images_data):
                try:
                    PostImage.objects.create(
                        post=post,
                        image_url=image,
                        order=order
                    )
                except Exception as e:
                    pass  # Handle exception silently

        return post


class CommentSerializer(ItemSerializer):
    def get_replies(self, comment):
        child_comments = comment.replies.filter(active=True)
        return CommentSerializer(child_comments, many=True, context=self.context).data

    def get_liked(self, comment):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return LikeComment.objects.filter(comment=comment, user=request.user, active=True).exists()

    def to_representation(self, instance):
        data = super().to_representation(instance)
        data['user'] = UserSerializer(instance.user).data
        data['like'] = self.get_liked(instance)
        data['replies'] = self.get_replies(instance)
        if instance.parent:
            data['parent_id'] = instance.parent.id
        return data

    class Meta:
        model = Comment
        fields = ['id', 'post', 'user', 'content', 'parent', 'created_date']
        extra_kwargs = {
            'post': {'write_only': True},
            'parent': {'write_only': True}
        }


class SearchHistorySerializer(serializers.ModelSerializer):
    class Meta:
        model = SearchHistory
        fields = ['id', 'search_params', 'created_date']
        read_only_fields = ['user', 'created_date']


class NotificationSerializer(ItemSerializer):
    class Meta:
        model = Notifications
        fields = ['id', 'receiver', 'title', 'content', 'is_read', 'notification_type', 'created_date']
        read_only_fields = ['id', 'created_date']

    def to_representation(self, instance):
        data = super().to_representation(instance)
        data['receiver'] = UserSerializer(instance.receiver).data
        return data


class ChatRoomSerializer(ItemSerializer):
    participants = UserSerializer(many=True, read_only=True)
    last_message = serializers.SerializerMethodField()
    unread_count = serializers.SerializerMethodField()

    class Meta:
        model = ChatRoom
        fields = ['id', 'name', 'participants', 'created_date', 'updated_date', 'last_message', 'unread_count']
        read_only_fields = ['created_date', 'updated_date']

    def get_last_message(self, obj):
        last_message = obj.messages.filter(active=True).order_by('-created_date').first()
        if last_message:
            return MessageSerializer(last_message).data
        return None

    def get_unread_count(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return obj.messages.filter(active=True, is_read=False).exclude(sender=request.user).count()
        return 0


class MessageSerializer(serializers.ModelSerializer):
    sender = UserSerializer(read_only=True)
    chat_room = serializers.PrimaryKeyRelatedField(read_only=True)

    class Meta:
        model = Message
        fields = ['id', 'content', 'sender', 'chat_room', 'is_read', 'created_date']
        read_only_fields = ['sender', 'created_date']


class FollowSerializer(serializers.ModelSerializer):
    followed_user = UserSerializer(read_only=True)
    follower_user = UserSerializer(read_only=True)

    class Meta:
        model = Follow
        fields = ['id', 'followed_user', 'follower_user', 'last_message_time']
        read_only_fields = ['id', 'last_message_time']

    def to_representation(self, instance):
        data = super().to_representation(instance)
        # Thêm thông tin chi tiết của người được theo dõi
        data['followed_user'] = UserSerializer(instance.followed_user).data
        # Thêm thông tin chi tiết của người theo dõi
        data['follower_user'] = UserSerializer(instance.follower_user).data
        return data


class PaymentSerializer(serializers.ModelSerializer):
    payer = serializers.SlugRelatedField(
        slug_field='username',
        read_only=True
    )
    room = serializers.PrimaryKeyRelatedField(
        queryset=Room.objects.all()
    )

    class Meta:
        model = Payment
        fields = ['id', 'payer', 'room', 'amount', 'payment_method', 'status', 'description', 'vnp_transaction_no', 'vnp_bank_code', 'vnp_bank_tran_no', 'vnp_card_type', 'vnp_pay_date', 'vnp_response_code', 'vnp_txn_ref', 'created_date', 'updated_date']
        read_only_fields = ['id', 'payer', 'created_date', 'updated_date']


class MotelImageSerializer(ItemSerializer):
    class Meta:
        model = MotelImage
        fields = ['id', 'motel', 'image_url', 'image_type', 'created_date', 'updated_date', 'active']

    def to_representation(self, instance):
        data = super().to_representation(instance)
        data['image_url'] = instance.image_url.url if instance.image_url else None
        return data


class RoomImageSerializer(ItemSerializer):
    class Meta:
        model = RoomImage
        fields = ['id', 'room', 'image_url', 'created_date', 'updated_date', 'active']

    def to_representation(self, instance):
        data = super().to_representation(instance)
        data['image_url'] = instance.image_url.url if instance.image_url else None
        return data


class AmenitySerializer(ItemSerializer):
    class Meta:
        model = Amenity
        fields = ['id', 'name']


class FavoriteSerializer(ItemSerializer):
    motel = MotelSerializer(read_only=True)
    user = UserSerializer(read_only=True)

    class Meta:
        model = Favorite
        fields = ['id', 'user', 'motel', 'created_date', 'updated_date', 'active']
        read_only_fields = ['user', 'created_date', 'updated_date']
