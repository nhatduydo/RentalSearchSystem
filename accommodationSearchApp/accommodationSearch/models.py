import json
import uuid

from autoslug import AutoSlugField
from ckeditor.fields import RichTextField
from cloudinary.models import CloudinaryField
from django.contrib.auth.models import AbstractUser
from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import Count
from django.utils.text import slugify
from django.utils.timezone import now
from unidecode import unidecode


class UserRole(models.TextChoices):
    ADMIN = "ADMIN", 'Admin'
    LANDLORD = "LANDLORD", "Landlord"
    TENANT = "TENANT", "Tenant"


class Gender(models.TextChoices):
    MALE = "MALE", "Male"
    FEMALE = "FEMALE", "Female"
    OTHER = "OTHER", "Other"


class ImageType(models.TextChoices):
    INSIDE = "INSIDE", "Inside"
    OUTSIDE = "OUTSIDE", "Outside"


class PostType(models.TextChoices):
    RENT_OUT = "RENT_OUT", "Rent Out"
    FIND_ROOM = "FIND_ROOM", "Find Room"


class NotificationType(models.TextChoices):
    NEW_POST = "NEW_POST", "New Post"
    NEW_COMMENT = "NEW_COMMENT", "New Comment"
    NEW_MOTEL = "NEW_MOTEL", "New Motel"
    COMMENT_LIKE = "COMMENT_LIKE", "Comment Like"
    VERIFICATION_SUCCESS = "VERIFICATION_SUCCESS", "Verification Success"
    MOTEL_UPDATE = "MOTEL_UPDATE", "Motel Update"
    MOTEL_LIKE = "MOTEL_LIKE", "Motel Like"
    FOLLOW = "FOLLOW", "Follow"
    PAYMENT = "PAYMENT", "Payment"
    SYSTEM = "SYSTEM", "System"


class PaymentMethod(models.TextChoices):
    VNPAY = "VNPAY", "Vnpay"
    STRIPE = "STRIPE", "Stripe"
    CASH = "CASH", "Cash"


class RoomStatus(models.TextChoices):
    ACTIVE = "ACTIVE", "Active"
    EXPIRED = "EXPIRED", "Expired"
    CANCELLED = "CANCELLED", "Cancelled"
    PENDING = "PENDING", "Pending"


class PaymentStatus(models.TextChoices):
    PENDING = "PENDING", "Pending"
    COMPLETED = "COMPLETED", "Completed"
    FAILED = "FAILED", "Failed"


class RoomTenantStatus(models.TextChoices):
    ACTIVE = "ACTIVE", "Active"
    EXPIRED = "EXPIRED", "Expired"
    CANCELLED = "CANCELLED", "Cancelled"
    PENDING = "PENDING", "Pending"


class BaseModel(models.Model):
    created_date = models.DateTimeField(auto_now_add=True)
    updated_date = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class ActiveModel(BaseModel):
    active = models.BooleanField(default=True)

    class Meta:
        abstract = True


class SlugModel(ActiveModel):
    slug = AutoSlugField(populate_from='slug_source', unique=True, null=True)

    def save(self, *args, **kwargs):
        if not self.slug and hasattr(self, "slug_source"):
            value = getattr(self, self.slug_source, None)
            if value:
                self.slug = slugify(unidecode(value))
        super().save(*args, **kwargs)

    class Meta:
        abstract = True


class InformationUserModel(SlugModel):
    full_name = models.CharField(max_length=255)
    citizen_id = models.CharField(max_length=20, unique=True)
    phone = models.CharField(max_length=20, null=True)
    address = models.TextField(blank=True, null=True)
    date_of_birth = models.DateField(blank=True, null=True)
    gender = models.CharField(max_length=20, choices=Gender.choices, null=True)
    bank_account = models.CharField(max_length=100, blank=True, null=True)

    class Meta:
        abstract = True


class User(AbstractUser):
    id = models.AutoField(primary_key=True)
    role = models.CharField(max_length=20, choices=UserRole.choices)
    date_joined = models.DateTimeField(default=now)
    slug = AutoSlugField(populate_from='username', unique=True, null=True)
    created_date = models.DateTimeField(auto_now_add=True)
    updated_date = models.DateTimeField(auto_now=True)
    avatar = CloudinaryField(null=True)
    email = models.EmailField(unique=True)
    last_login = None

    class Meta:
        verbose_name = "User"
        verbose_name_plural = "User"

    def __str__(self):
        return self.username

    def clean(self):
        super().clean()
        if self.role in ['LANDLORD', 'TENANT'] and not self.avatar:
            raise ValidationError({
                'avatar': 'Avatar là bắt buộc cho chủ trọ và người thuê trọ'
            })

    def save(self, *args, **kwargs):
        self.full_clean()  # Gọi clean() trước khi save
        super().save(*args, **kwargs)


class Admin(ActiveModel):
    user = models.OneToOneField(User, on_delete=models.CASCADE, primary_key=True)

    def email(self):
        return self.user.email


class Landlord(InformationUserModel):
    user = models.OneToOneField(User, on_delete=models.CASCADE, primary_key=True,  related_name='landlord_profile')
    is_verified = models.BooleanField(default=False)
    slug_source = "full_name"

    def __str__(self):  # hiển thị tên đại diện của đối tượng khi in ra hoặc hiển thị trong admin.
        return self.full_name

    def email(self):
        return self.user.email  # Trả về địa chỉ email từ đối tượng user liên kết

    class Meta:
        verbose_name = "Chủ nhà trọ"
        verbose_name_plural = "Chủ nhà trọ"


class Tenant(InformationUserModel):
    user = models.OneToOneField(User, on_delete=models.CASCADE, primary_key=True,  related_name="tenant_profile")
    rooms = models.ManyToManyField('Room', through='RoomTenant', related_name='roomer')
    slug_source = "full_name"

    def __str__(self):
        return self.full_name

    def email(self):
        return self.user.email

    class Meta:
        verbose_name = "Người thuê trọ"
        verbose_name_plural = "Người thuê trọ"


class Motel(SlugModel):
    id = models.AutoField(primary_key=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='motels')
    motel_name = models.CharField(max_length=255)
    slug_source = "motel_name"
    description = models.TextField()
    address = models.TextField()
    district = models.CharField(max_length=255, null=True, blank=True)
    city = models.CharField(max_length=255)
    province = models.CharField(max_length=255, null=True, blank=True)
    longitude = models.FloatField(null=True, blank=True)
    latitude = models.FloatField(null=True, blank=True)
    total_rooms = models.IntegerField()
    available_rooms = models.IntegerField()
    rating_score = models.FloatField(default=0)
    is_verified = models.BooleanField(default=False)

    def clean(self):
        if self.user.role == 'LANDLORD':
            try:
                landlord = Landlord.objects.get(user=self.user)
            except Landlord.DoesNotExist:
                raise ValidationError('Không tìm thấy thông tin chủ trọ')

        if not landlord.phone:
            raise ValidationError('Chủ trọ cần có số điện thoại')
        if not self.address:
            raise ValidationError('Nhà trọ cần có địa chỉ')

    def check_verification(self):
        try:
            # Kiểm tra số lượng hình ảnh
            active_images_count = self.images.filter(active=True).count()
            if active_images_count < 3:
                raise ValidationError('Nhà trọ cần có ít nhất 3 hình ảnh để được xác minh')

            # Kiểm tra địa chỉ đầy đủ
            has_valid_address = bool(self.address and self.district and (self.city or self.province))
            if not has_valid_address:
                raise ValidationError('Nhà trọ cần có địa chỉ đầy đủ để được xác minh')

            # Kiểm tra số điện thoại chủ trọ
            has_valid_phone = bool(self.user.landlord_profile.phone)
            if not has_valid_phone:
                raise ValidationError('Chủ trọ cần có số điện thoại để được xác minh')

            return True
        except ValidationError:
            return False

    def save(self, *args, **kwargs):
        self.full_clean()  # Validate basic fields
        super().save(*args, **kwargs)

    def __str__(self):
        return self.motel_name

    class Meta:
        verbose_name = "Nhà trọ"
        verbose_name_plural = "Nhà trọ"
        ordering = ['-created_date']


class Room(SlugModel):
    id = models.AutoField(primary_key=True)
    motel = models.ForeignKey(Motel, on_delete=models.CASCADE, related_name='rooms')
    room_name = models.CharField(max_length=255)
    description = models.TextField()
    area = models.FloatField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    max_people = models.IntegerField()
    tenants = models.ManyToManyField('Tenant', through='RoomTenant', related_name='rented_rooms')
    amenities = models.ManyToManyField('Amenity')
    is_verified = models.BooleanField(default=False)

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(unidecode(f"{self.motel.motel_name}-{self.room_name}"))
        super().save(*args, **kwargs)

    def check_verification(self):
        if self.images.count() < 3:
            self.is_verified = False
        else:
            self.is_verified = True
        self.save()

    class Meta:
        unique_together = ('room_name', 'motel')
        verbose_name = "Phòng trọ"
        verbose_name_plural = "Phòng trọ"

    def __str__(self):
        return self.room_name
        # return f"{self.motel.motel_name} - {self.room_name}"


class Amenity(SlugModel):
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=255, unique=True)
    slug_source = "name"

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Tiện nghi, tiện ích"
        verbose_name_plural = "Tiện nghi, tiện ích"


class MotelImage(ActiveModel):
    id = models.AutoField(primary_key=True)
    motel = models.ForeignKey(Motel, on_delete=models.CASCADE, related_name="images")
    image_url = CloudinaryField('image')
    image_type = models.CharField(max_length=20, choices=ImageType.choices)

    def __str__(self):
        return f"Image for {self.motel.motel_name}"

    class Meta:
        verbose_name = 'hình ảnh'
        verbose_name_plural = "Hình ảnh nhà trọ"


class RoomImage(ActiveModel):
    id = models.AutoField(primary_key=True)
    room = models.ForeignKey(Room, on_delete=models.CASCADE, related_name="images")
    image_url = CloudinaryField('image')

    def __str__(self):
        return f"Image for {self.room.room_name}"

    class Meta:
        verbose_name = 'hình ảnh'
        verbose_name_plural = "Hình ảnh phòng trọ"


class RoomTenant(ActiveModel):
    id = models.AutoField(primary_key=True)
    room = models.ForeignKey(Room, on_delete=models.CASCADE, related_name='tenant_entries')
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, related_name='room_entries')
    start_date = models.DateField()
    end_date = models.DateField()
    status = models.CharField(max_length=20, choices=RoomTenantStatus.choices)
    is_paid = models.BooleanField(default=False)

    def __str__(self):
        return f"RoomTenant for {self.room.room_name} with {self.tenant.full_name}"


class MotelRating(ActiveModel):
    id = models.AutoField(primary_key=True)
    motel = models.ForeignKey(Motel, on_delete=models.CASCADE, related_name='motel_ratings')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='user_ratings', null=True, blank=True)
    rating = models.IntegerField()
    comment = models.TextField()

    class Meta:
        verbose_name = 'Đánh giá'
        verbose_name_plural = 'Đánh giá'
        unique_together = ['motel', 'user']


class Favorite(ActiveModel):
    id = models.AutoField(primary_key=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='favorites')
    motel = models.ForeignKey(Motel, on_delete=models.CASCADE, related_name='favorited_by')

    class Meta:
        unique_together = ('user', 'motel')
        verbose_name = "Yêu thích"
        verbose_name_plural = "Yêu thích"

    def __str__(self):
        return f"{self.user.username} favorite {self.motel.motel_name}"


class Post(SlugModel):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    post_type = models.CharField(max_length=20, choices=PostType.choices)
    title = models.CharField(max_length=255)
    slug_source = models.CharField(max_length=255, default="title")
    content = RichTextField()
    desired_address = models.TextField(blank=True, null=True)
    min_price = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    max_price = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    radius_km = models.FloatField(blank=True, null=True)
    desired_latitude = models.FloatField(blank=True, null=True)
    desired_longitude = models.FloatField(blank=True, null=True)
    motel = models.ForeignKey(Motel, on_delete=models.CASCADE, blank=True, null=True)

    class Meta:
        verbose_name = "Post"
        verbose_name_plural = "Bài Post"

    def __str__(self):
        return self.title


class PostImage(ActiveModel):
    id = models.AutoField(primary_key=True)
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name="images")
    image_url = CloudinaryField('image')
    image_type = models.CharField(max_length=20, choices=ImageType.choices, default=ImageType.INSIDE)
    order = models.IntegerField(default=0)  # Để sắp xếp thứ tự hiển thị ảnh

    class Meta:
        verbose_name = 'Hình ảnh bài đăng'
        verbose_name_plural = "Hình ảnh bài đăng"
        ordering = ['order']

    def __str__(self):
        return f"Image for {self.post.title}"


class Comment(ActiveModel):
    id = models.AutoField(primary_key=True)
    post = models.ForeignKey(Post, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    content = models.TextField(blank=True, null=True)
    parent = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True,  related_name='replies')

    # def __str__(self):
    #     return self.post.title

    def __str__(self):
        return f'Comment by {self.user} on {self.post}'

    class Meta:
        verbose_name = "Bình Luận"
        verbose_name_plural = "Bình luận"


class LikeComment(ActiveModel):
    id = models.AutoField(primary_key=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='users')
    comment = models.ForeignKey(Comment, on_delete=models.CASCADE)

    def __str__(self):
        return self.comment.post.title

    class Meta:
        unique_together = ('user', 'comment')
        verbose_name = "Like bình luận"
        verbose_name_plural = "Like bình luận"


class LikeMotel(ActiveModel):
    id = models.AutoField(primary_key=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    motel = models.ForeignKey(Motel, on_delete=models.CASCADE)

    class Meta:
        unique_together = ('user', 'motel')
        verbose_name = "Like nhà trọ"
        verbose_name_plural = "Like nhà trọ"

    def __str__(self):
        return self.user.username


class SearchHistory(ActiveModel):
    id = models.AutoField(primary_key=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="search_histories")
    search_params = models.JSONField()

    def __str__(self):
        return f"Search by {self.user.username} on {self.created_date}"

    # Hàm kiểm tra nếu search_params là chuỗi (str) thì dùng json.loads() để chuyển chuỗi JSON thành dict.
    def get_search_params(self):
        return json.loads(self.search_params) if isinstance(self.search_params, str) else self.search_params

    def set_search_params(self, params_dict):
        self.search_params = json.dumps(params_dict)
        self.save()

    class Meta:
        verbose_name = "Lịch sử tìm kiếm"
        verbose_name_plural = "Lịch sử tìm kiếm"


class Follow(ActiveModel):
    id = models.AutoField(primary_key=True)
    followed_user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='followers')  # Người được theo dõi
    follower_user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='following')  # Người đi theo dõi
    last_message_time = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('followed_user', 'follower_user')
        verbose_name = "Theo dõi"
        verbose_name_plural = "Theo dõi"


class Notifications(ActiveModel):
    id = models.AutoField(primary_key=True)
    receiver = models.ForeignKey(User, on_delete=models.CASCADE)
    title = models.CharField(max_length=255)
    content = models.TextField()
    is_read = models.BooleanField(default=False)
    notification_type = models.CharField(max_length=20, choices=NotificationType.choices)
    related_object_id = models.CharField(max_length=36, null=True, blank=True)

    def __str__(self):
        return self.title

    class Meta:
        verbose_name = "Thông báo"
        verbose_name_plural = "Thông báo"


class ChatRoom(ActiveModel):
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=255, null=True, blank=True)  # Tên phòng chat (cho nhóm)
    participants = models.ManyToManyField(User, related_name="chat_rooms")

    def __str__(self):
        if self.name:
            return self.name
        participants = self.participants.all()
        if len(participants) == 2:
            return f"{participants[0].username} - {participants[1].username}"
        return f"Group chat with {len(participants)} participants"


class Message(ActiveModel):
    id = models.AutoField(primary_key=True)
    chat_room = models.ForeignKey(ChatRoom, on_delete=models.CASCADE, related_name="messages")
    sender = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sent_messages')
    content = models.TextField()
    is_read = models.BooleanField(default=False)

    def __str__(self):
        return f"Message from {self.sender.username} in {self.chat_room}"


class Payment(ActiveModel):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    payer = models.ForeignKey(User, on_delete=models.CASCADE, related_name='paid_payments')
    room = models.ForeignKey(Room, on_delete=models.CASCADE, related_name='room_payments')
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    payment_method = models.CharField(max_length=20, choices=PaymentMethod.choices)
    status = models.CharField(max_length=20, choices=PaymentStatus.choices)
    description = models.TextField(null=True, blank=True)
    # VNPay specific fields
    vnp_transaction_no = models.CharField(max_length=15, null=True, blank=True)  # Mã giao dịch do VNPay cấp.
    vnp_bank_code = models.CharField(max_length=20, null=True, blank=True)  # Mã ngân hàng thanh toán.
    vnp_bank_tran_no = models.CharField(max_length=255, null=True, blank=True)  # Mã giao dịch tại ngân hàng.
    vnp_card_type = models.CharField(max_length=20, null=True, blank=True)  # Loại thẻ (ATM, VISA, v.v.).
    vnp_pay_date = models.DateTimeField(null=True, blank=True)  # Ngày thanh toán.
    vnp_response_code = models.CharField(max_length=2, null=True, blank=True)  # Mã phản hồi của VNPay (00 là thành công).
    vnp_txn_ref = models.CharField(max_length=100, null=True, blank=True)  # Mã tham chiếu giao dịch (do hệ thống của bạn tạo).

    class Meta:
        verbose_name = "Thanh toán"
        verbose_name_plural = "Thanh toán"
