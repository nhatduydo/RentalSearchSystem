from accommodationSearch.models import (Amenity, ChatRoom, Comment, Favorite,
                                        Follow, Landlord, LikeComment,
                                        LikeMotel, Message, Motel, MotelImage,
                                        MotelRating, Notifications,
                                        NotificationType, Payment, Post,
                                        PostImage, Room, RoomImage, RoomTenant,
                                        RoomTenantStatus, SearchHistory,
                                        Tenant, User)
from rest_framework import serializers
from rest_framework.serializers import ModelSerializer


class ItemSerializer(ModelSerializer):
    """
    Serializer cơ sở cho các đối tượng có hình ảnh
    Tự động chuyển đổi URL của hình ảnh thành đường dẫn đầy đủ
    """

    def to_representation(self, instance):
        """
        Override phương thức to_representation để tự động chuyển đổi URL hình ảnh
        Args:
            instance: Instance của model cần serialize
        Returns:
            dict: Dữ liệu đã được serialize với URL hình ảnh đầy đủ
        """
        data = super().to_representation(instance)
        if hasattr(instance, 'image') and instance.image:
            data['image'] = instance.image.url
        if hasattr(instance, 'avatar') and instance.avatar:
            data['avatar'] = instance.avatar.url
        return data


class UserSerializer(ItemSerializer):
    """
    Serializer cho model User
    Xử lý việc mã hóa mật khẩu và hiển thị thông tin người dùng
    """
    class Meta:
        model = User
        fields = ['id', 'username', 'password', 'email', 'first_name', 'last_name', 'role', 'created_date', 'avatar']
        extra_kwargs = {
            'password': {
                'write_only': True  # Mật khẩu chỉ được ghi, không được đọc
            }
        }

    def validate_password(self, value):
        """
        Kiểm tra độ mạnh của mật khẩu
        Yêu cầu mật khẩu ít nhất 8 ký tự cho LANDLORD và TENANT
        Args:
            value: Giá trị mật khẩu cần validate
        Returns:
            str: Mật khẩu đã được validate
        Raises:
            ValidationError: Nếu mật khẩu không đủ mạnh
        """
        role = self.initial_data.get('role')
        if role in ['LANDLORD', 'TENANT']:
            if len(value) < 8:
                raise serializers.ValidationError("Mật khẩu phải có ít nhất 8 ký tự ")
        return value

    def to_representation(self, instance):
        """
        Chuyển đổi URL avatar thành đường dẫn đầy đủ
        Args:
            instance: Instance của User model
        Returns:
            dict: Dữ liệu user với URL avatar đầy đủ
        """
        data = super().to_representation(instance)
        if instance.avatar:
            data['avatar'] = instance.avatar.url
        return data

    def create(self, validated_data):
        """
        Tạo user mới với mật khẩu đã được mã hóa
        Args:
            validated_data: Dữ liệu đã được validate
        Returns:
            User: Instance của User đã được tạo
        """
        password = validated_data.pop('password')
        user = User(**validated_data)
        user.set_password(password)  # Mã hóa mật khẩu trước khi lưu
        user.save()
        return user

    def update(self, instance, validated_data):
        """
        Cập nhật thông tin user, bao gồm cả mật khẩu nếu có
        Args:
            instance: Instance của User cần cập nhật
            validated_data: Dữ liệu đã được validate
        Returns:
            User: Instance của User đã được cập nhật
        """
        password = validated_data.pop('password', None)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)

        if password:
            instance.set_password(password)  # Mã hóa mật khẩu mới nếu có

        instance.save()
        return instance


class LandlordSerializer(ItemSerializer):
    """
    Serializer cho model Landlord (Chủ nhà)
    """
    class Meta:
        model = Landlord
        fields = ['user', 'full_name', 'citizen_id', 'phone', 'address', 'date_of_birth', 'gender', 'bank_account', 'is_verified']
        read_only_fields = ['is_verified']  # Trường xác thực chỉ được đọc


class TenantSerializer(ItemSerializer):
    """
    Serializer cho model Tenant (Người thuê)
    """
    class Meta:
        model = Tenant
        fields = ['user', 'full_name', 'citizen_id', 'phone', 'address', 'date_of_birth', 'gender', 'bank_account', 'rooms']

    def to_representation(self, instance):
        """
        Loại bỏ các phòng trùng lặp trong danh sách phòng
        Args:
            instance: Instance của Tenant model
        Returns:
            dict: Dữ liệu tenant với danh sách phòng không trùng lặp
        """
        data = super().to_representation(instance)
        if 'rooms' in data:
            data['rooms'] = list(set(data['rooms']))
        return data


class MotelSerializer(ItemSerializer):
    """
    Serializer cho model Motel (Nhà trọ)
    Bao gồm thông tin về trạng thái like và favorite
    """

    def get_liked(self, motel):
        """
        Kiểm tra xem người dùng hiện tại có like nhà trọ này không
        Args:
            motel: Instance của Motel model
        Returns:
            bool: True nếu đã like, False nếu chưa
        """
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return LikeMotel.objects.filter(motel=motel, user=request.user, active=True).exists()

    def get_favorite(self, motel):
        """
        Kiểm tra xem người dùng hiện tại có đánh dấu nhà trọ này là favorite không
        Args:
            motel: Instance của Motel model
        Returns:
            bool: True nếu đã đánh dấu favorite, False nếu chưa
        """
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return Favorite.objects.filter(motel=motel, user=request.user, active=True).exists()

    def to_representation(self, instance):
        """
        Thêm thông tin user, trạng thái like và favorite vào dữ liệu
        Args:
            instance: Instance của Motel model
        Returns:
            dict: Dữ liệu nhà trọ với thông tin bổ sung
        """
        data = super().to_representation(instance)
        data['user'] = UserSerializer(instance.user).data
        data['like'] = self.get_liked(instance)
        data['favorite'] = self.get_favorite(instance)
        return data

    class Meta:
        model = Motel
        fields = ['id', 'user', 'motel_name', 'description', 'address', 'district', 'city', 'province', 'longitude', 'latitude', 'total_rooms', 'available_rooms', 'rating_score', 'is_verified']
        read_only_fields = ['user', 'rating_score', 'is_verified']


class RoomSerializer(ItemSerializer):
    """
    Serializer cho model Room (Phòng trọ)
    Bao gồm thông tin về tiện nghi và danh sách người thuê

    Fields:
        - id: ID của phòng
        - motel: Nhà trọ chứa phòng (ForeignKey)
        - room_name: Tên phòng
        - description: Mô tả
        - area: Diện tích
        - price: Giá phòng
        - max_people: Số người tối đa
        - tenants: Danh sách người thuê (ManyToMany)
        - amenities: Danh sách tiện nghi (ManyToMany)
        - amenities_display: Thông tin chi tiết về tiện nghi (SerializerMethodField)
        - is_verified: Trạng thái xác thực
    """
    # PrimaryKeyRelatedField: Chỉ lưu ID của các đối tượng liên quan
    # many=True: Cho phép nhiều đối tượng
    # queryset: Chỉ định tập hợp đối tượng có thể chọn
    amenities = serializers.PrimaryKeyRelatedField(many=True, queryset=Amenity.objects.all())

    # SerializerMethodField: Trường được tính toán bởi một method
    # Sẽ gọi method get_amenities_display để lấy giá trị
    amenities_display = serializers.SerializerMethodField()

    class Meta:
        model = Room
        fields = [
            'id', 'motel', 'room_name', 'description', 'area', 'price', 'max_people',
            'tenants', 'amenities', 'amenities_display', 'is_verified'
        ]

    def get_amenities_display(self, obj):
        """
        Lấy thông tin chi tiết về các tiện nghi của phòng
        Args:
            obj: Instance của Room model
        Returns:
            list: Danh sách thông tin chi tiết về tiện nghi
        """
        return AmenitySerializer(obj.amenities.all(), many=True).data

    def to_representation(self, instance):
        """
        Loại bỏ các người thuê trùng lặp trong danh sách
        Args:
            instance: Instance của Room model
        Returns:
            dict: Dữ liệu phòng với danh sách người thuê không trùng lặp
        """
        data = super().to_representation(instance)
        if 'tenants' in data:
            data['tenants'] = list(set(data['tenants']))
        return data


class AmenitySerializer(ItemSerializer):
    """
    Serializer cho model Amenity (Tiện nghi)
    """
    class Meta:
        model = Amenity
        fields = ['id', 'name']


class MotelImageSerializer(ItemSerializer):
    """
    Serializer cho model MotelImage (Hình ảnh nhà trọ)
    """
    class Meta:
        model = MotelImage
        fields = ['id', 'motel', 'image_url', 'image_type', 'created_date', 'updated_date', 'active']

    def to_representation(self, instance):
        """
        Chuyển đổi URL hình ảnh thành đường dẫn đầy đủ
        Args:
            instance: Instance của MotelImage model
        Returns:
            dict: Dữ liệu hình ảnh với URL đầy đủ
        """
        data = super().to_representation(instance)
        data['image_url'] = instance.image_url.url if instance.image_url else None
        return data


class RoomImageSerializer(ItemSerializer):
    """
    Serializer cho model RoomImage (Hình ảnh phòng trọ)
    """
    class Meta:
        model = RoomImage
        fields = ['id', 'room', 'image_url', 'created_date', 'updated_date', 'active']

    def to_representation(self, instance):
        """
        Chuyển đổi URL hình ảnh thành đường dẫn đầy đủ
        """
        data = super().to_representation(instance)
        data['image_url'] = instance.image_url.url if instance.image_url else None
        return data


class RoomTenantSerializer(ItemSerializer):
    """
    Serializer cho model RoomTenant (Quan hệ giữa phòng và người thuê)
    """
    class Meta:
        model = RoomTenant
        fields = ['id', 'room', 'tenant', 'start_date', 'end_date', 'status',
                  'is_paid', 'created_date', 'updated_date']
        read_only_fields = ['tenant', 'status', 'is_paid', 'created_date',
                            'updated_date']

    def to_representation(self, instance):
        """
        Thêm thông tin chi tiết về phòng và người thuê
        """
        data = super().to_representation(instance)
        data['room'] = RoomSerializer(instance.room).data
        data['tenant'] = TenantSerializer(instance.tenant).data
        return data

    def validate(self, data):
        """
        Kiểm tra tính hợp lệ của ngày bắt đầu và kết thúc
        """
        if data.get('start_date') and data.get('end_date'):
            if data['start_date'] > data['end_date']:
                raise serializers.ValidationError("Ngày bắt đầu phải trước ngày kết thúc")
        return data

    def validate_status(self, value):
        """
        Kiểm tra tính hợp lệ của trạng thái
        Args:
            value: Giá trị trạng thái cần validate
        Returns:
            str: Trạng thái đã được validate
        Raises:
            ValidationError: Nếu trạng thái không hợp lệ
        """
        if value not in dict(RoomTenantStatus.choices):
            raise serializers.ValidationError("Trạng thái không hợp lệ")
        return value


class MotelRatingSerializer(ItemSerializer):
    """
    Serializer cho model MotelRating (Đánh giá nhà trọ)
    """
    class Meta:
        model = MotelRating
        fields = ['id', 'motel', 'user', 'rating', 'comment', 'created_date']
        read_only_fields = ['id', 'created_date']

    def validate_rating(self, value):
        """
        Kiểm tra tính hợp lệ của điểm đánh giá (1-5)
        Args:
            value: Điểm đánh giá cần validate
        Returns:
            int: Điểm đánh giá đã được validate
        Raises:
            ValidationError: Nếu điểm không nằm trong khoảng 1-5
        """
        if value < 1 or value > 5:
            raise serializers.ValidationError("Xếp hạng phải nằm trong khoảng từ 1 đến 5")
        return value

    def to_representation(self, instance):
        """
        Thêm thông tin chi tiết về người đánh giá và nhà trọ
        Args:
            instance: Instance của MotelRating model
        Returns:
            dict: Dữ liệu đánh giá với thông tin chi tiết
        """
        data = super().to_representation(instance)
        data['user'] = UserSerializer(instance.user).data
        data['motel'] = MotelSerializer(instance.motel).data
        return data


class FavoriteSerializer(ItemSerializer):
    """
    Serializer cho model Favorite (Nhà trọ yêu thích)

    Fields:
        - id: ID của favorite
        - user: Người dùng (ForeignKey, read_only)
        - motel: Nhà trọ (ForeignKey, read_only)
        - motel_id: ID của nhà trọ (write_only)
        - created_date: Ngày tạo
        - updated_date: Ngày cập nhật
        - active: Trạng thái hoạt động
    """
    # Serializer lồng nhau: Sử dụng MotelSerializer để serialize trường motel
    motel = MotelSerializer(read_only=True)
    user = UserSerializer(read_only=True)
    # SlugRelatedField: Cho phép ghi ID của nhà trọ thay vì object
    motel_id = serializers.IntegerField(write_only=True)

    class Meta:
        model = Favorite
        fields = ['id', 'user', 'motel', 'motel_id', 'created_date', 'updated_date', 'active']
        read_only_fields = ['user', 'created_date', 'updated_date']


class PostImageSerializer(ItemSerializer):
    """
    Serializer cho model PostImage (Hình ảnh bài đăng)
    """
    class Meta:
        model = PostImage
        fields = ['id', 'image_url', 'image_type', 'order']

    def to_representation(self, instance):
        """
        Chuyển đổi URL hình ảnh thành đường dẫn đầy đủ
        Args:
            instance: Instance của PostImage model
        Returns:
            dict: Dữ liệu hình ảnh với URL đầy đủ
        """
        data = super().to_representation(instance)
        if instance.image_url:
            data['image_url'] = instance.image_url.url
        return data


class PostSerializer(ItemSerializer):
    """
    Serializer cho model Post (Bài đăng)
    Bao gồm số lượng bình luận và hình ảnh
    """
    # Serializer lồng nhau: Sử dụng UserSerializer để serialize trường user
    user = UserSerializer(read_only=True)
    # SerializerMethodField: Trường được tính toán bởi method get_comments_count
    comments_count = serializers.SerializerMethodField()
    # Nested serializer: Sử dụng PostImageSerializer để serialize danh sách hình ảnh
    images = PostImageSerializer(many=True, read_only=True)

    class Meta:
        model = Post
        fields = ['id', 'user', 'post_type', 'title', 'content', 'created_date',
                  'min_price', 'max_price', 'comments_count', 'images']

    def get_comments_count(self, obj):
        """
        Đếm số lượng bình luận của bài đăng
        Args:
            obj: Instance của Post model
        Returns:
            int: Số lượng bình luận
        """
        return Comment.objects.filter(post=obj).count()


class PostDetailSerializer(ItemSerializer):
    """
    Serializer chi tiết cho model Post
    Bao gồm thông tin về bình luận và hình ảnh
    """
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
        """
        Lấy danh sách bình luận gốc (không phải reply)
        Args:
            obj: Instance của Post model
        Returns:
            list: Danh sách bình luận gốc
        """
        comments = Comment.objects.filter(post=obj, parent=None)
        return CommentSerializer(comments, many=True, context=self.context).data

    def get_comments_count(self, obj):
        """
        Đếm tổng số bình luận
        Args:
            obj: Instance của Post model
        Returns:
            int: Tổng số bình luận
        """
        return Comment.objects.filter(post=obj).count()

    def create(self, validated_data):
        """
        Tạo bài đăng mới và xử lý upload hình ảnh
        Args:
            validated_data: Dữ liệu đã được validate
        Returns:
            Post: Instance của Post đã được tạo
        """
        request = self.context.get('request')
        images_data = request.FILES.getlist('images')

        post = super().create(validated_data)

        if images_data:
            for order, image in enumerate(images_data):
                try:
                    PostImage.objects.create(
                        post=post,
                        image_url=image,
                        order=order
                    )
                except Exception as e:
                    print("có lỗi xảy ra: ", e)
        return post


class CommentSerializer(ItemSerializer):
    """
    Serializer cho model Comment (Bình luận)
    Bao gồm thông tin về replies và trạng thái like
    """

    def get_replies(self, comment):
        """
        Lấy danh sách replies của bình luận
        Args:
            comment: Instance của Comment model
        Returns:
            list: Danh sách replies
        """
        child_comments = comment.replies.filter(active=True)
        return CommentSerializer(child_comments, many=True, context=self.context).data

    def get_liked(self, comment):
        """
        Kiểm tra xem người dùng hiện tại có like bình luận này không
        Args:
            comment: Instance của Comment model
        Returns:
            bool: True nếu đã like, False nếu chưa
        """
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return LikeComment.objects.filter(comment=comment, user=request.user, active=True).exists()

    def to_representation(self, instance):
        """
        Thêm thông tin về người bình luận, trạng thái like và replies
        Args:
            instance: Instance của Comment model
        Returns:
            dict: Dữ liệu bình luận với thông tin bổ sung
        """
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
    """
    Serializer cho model SearchHistory (Lịch sử tìm kiếm)

    Fields:
        - id: ID của lịch sử
        - search_params: Tham số tìm kiếm
        - created_date: Ngày tạo
    """
    class Meta:
        model = SearchHistory
        fields = ['id', 'search_params', 'created_date']
        read_only_fields = ['user', 'created_date']


class FollowSerializer(serializers.ModelSerializer):
    """
    Serializer cho model Follow (Theo dõi)

    Fields:
        - id: ID của quan hệ theo dõi
        - followed_user: Người được theo dõi (ForeignKey, read_only)
        - follower_user: Người theo dõi (ForeignKey, read_only)
        - last_message_time: Thời gian tin nhắn cuối cùng
    """
    # Serializer lồng nhau: Sử dụng UserSerializer để serialize các trường user
    followed_user = UserSerializer(read_only=True)
    follower_user = UserSerializer(read_only=True)

    class Meta:
        model = Follow
        fields = ['id', 'followed_user', 'follower_user', 'last_message_time']
        read_only_fields = ['id', 'last_message_time']

    def to_representation(self, instance):
        """
        Thêm thông tin chi tiết về người được theo dõi và người theo dõi
        Args:
            instance: Instance của Follow model
        Returns:
            dict: Dữ liệu quan hệ theo dõi với thông tin chi tiết
        """
        data = super().to_representation(instance)
        data['followed_user'] = UserSerializer(instance.followed_user).data
        data['follower_user'] = UserSerializer(instance.follower_user).data
        return data


class NotificationSerializer(ItemSerializer):
    """
    Serializer cho model Notifications (Thông báo)
    """
    class Meta:
        model = Notifications
        fields = ['id', 'receiver', 'title', 'content', 'is_read', 'notification_type', 'created_date']
        read_only_fields = ['id', 'created_date']

    def to_representation(self, instance):
        """
        Thêm thông tin chi tiết về người nhận thông báo
        Args:
            instance: Instance của Notifications model
        Returns:
            dict: Dữ liệu thông báo với thông tin chi tiết
        """
        data = super().to_representation(instance)
        data['receiver'] = UserSerializer(instance.receiver).data
        return data


class ChatRoomSerializer(ItemSerializer):
    """
    Serializer cho model ChatRoom (Phòng chat)
    Bao gồm thông tin về tin nhắn cuối cùng và số tin nhắn chưa đọc
    """
    # Serializer lồng nhau: Sử dụng UserSerializer để serialize danh sách người tham gia
    participants = UserSerializer(many=True, read_only=True)
    # SerializerMethodField: Trường được tính toán bởi method get_last_message
    last_message = serializers.SerializerMethodField()
    # SerializerMethodField: Trường được tính toán bởi method get_unread_count
    unread_count = serializers.SerializerMethodField()

    class Meta:
        model = ChatRoom
        fields = ['id', 'name', 'participants', 'created_date', 'updated_date', 'last_message', 'unread_count']
        read_only_fields = ['created_date', 'updated_date']

    def get_last_message(self, obj):
        """
        Lấy tin nhắn cuối cùng của phòng chat
        Args:
            obj: Instance của ChatRoom model
        Returns:
            dict: Thông tin tin nhắn cuối cùng
        """
        last_message = obj.messages.filter(active=True).order_by('-created_date').first()
        if last_message:
            return MessageSerializer(last_message).data
        return None

    def get_unread_count(self, obj):
        """
        Đếm số tin nhắn chưa đọc của người dùng hiện tại
        Args:
            obj: Instance của ChatRoom model
        Returns:
            int: Số tin nhắn chưa đọc
        """
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return obj.messages.filter(active=True, is_read=False).exclude(sender=request.user).count()
        return 0


class MessageSerializer(serializers.ModelSerializer):
    """
    Serializer cho model Message (Tin nhắn)
    """
    # Serializer lồng nhau: Sử dụng UserSerializer để serialize trường sender
    sender = UserSerializer(read_only=True)
    # PrimaryKeyRelatedField: Chỉ lưu ID của phòng chat
    chat_room = serializers.PrimaryKeyRelatedField(read_only=True)

    class Meta:
        model = Message
        fields = ['id', 'content', 'sender', 'chat_room', 'is_read', 'created_date']
        read_only_fields = ['sender', 'created_date']


class PaymentSerializer(serializers.ModelSerializer):
    """
    Serializer cho model Payment (Thanh toán)

    Fields:
        - id: ID của thanh toán
        - payer: Người thanh toán (SlugRelatedField, read_only)
        - room: Phòng (PrimaryKeyRelatedField)
        - amount: Số tiền
        - payment_method: Phương thức thanh toán
        - status: Trạng thái
        - description: Mô tả
        - vnp_transaction_no: Mã giao dịch VNPay
        - vnp_bank_code: Mã ngân hàng VNPay
        - vnp_bank_tran_no: Mã giao dịch ngân hàng VNPay
        - vnp_card_type: Loại thẻ VNPay
        - vnp_pay_date: Ngày thanh toán VNPay
        - vnp_response_code: Mã phản hồi VNPay
        - vnp_txn_ref: Mã tham chiếu VNPay
        - created_date: Ngày tạo
        - updated_date: Ngày cập nhật
    """
    # SlugRelatedField: Sử dụng username làm slug field
    payer = serializers.SlugRelatedField(
        slug_field='username',
        read_only=True
    )
    # PrimaryKeyRelatedField: Chỉ lưu ID của phòng
    room = serializers.PrimaryKeyRelatedField(
        queryset=Room.objects.all()
    )

    class Meta:
        model = Payment
        fields = ['id', 'payer', 'room', 'amount', 'payment_method', 'status', 'description', 'vnp_transaction_no', 'vnp_bank_code', 'vnp_bank_tran_no', 'vnp_card_type', 'vnp_pay_date', 'vnp_response_code', 'vnp_txn_ref', 'created_date', 'updated_date']
        read_only_fields = ['id', 'payer', 'created_date', 'updated_date']
