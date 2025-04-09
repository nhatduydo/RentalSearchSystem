from django.db import models
from autoslug import AutoSlugField
from django.contrib.auth.models import AbstractUser
from cloudinary.models import CloudinaryField
import uuid
import json
from ckeditor.fields import RichTextField
from django.db.models import Count
from django.utils.timezone import now
from django.utils.text import slugify
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
    ACCOUNT_VERIFICATION = "ACCOUNT_VERIFICATION", "Account Verification"
    MOTEL_UPDATE = "MOTEL_UPDATE", "Motel Update"
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
    slug = AutoSlugField(populate_from='slug_source', unique=True, null = True)
    
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
    phone = models.CharField(max_length=20, null = True)
    avatar = CloudinaryField(null = True)
    address = models.TextField(blank = True, null = True)
    date_of_birth = models.DateField(blank = True, null = True)
    gender = models.CharField(max_length=20, choices=Gender.choices, null = True)
    bank_account = models.CharField(max_length=100, blank = True, null = True)
    
    class Meta:
        abstract = True

#1 đã admin, đã serializer, đã API
class User(AbstractUser):
    id = models.AutoField(primary_key=True)
    role = models.CharField(max_length=20, choices=UserRole.choices)
    date_joined = models.DateTimeField(default=now)
    slug = AutoSlugField(populate_from = 'username', unique=True, null = True)
    created_date = models.DateTimeField(auto_now_add=True)
    updated_date = models.DateTimeField(auto_now=True)
    avatar = CloudinaryField(null=True)
    last_login = None
    # date_joined = None

    class Meta:
        verbose_name = "User"
        verbose_name_plural = "User"
        
    def __str__(self):
        return self.username
    
#2 chưa biết có phải cho qua trang admin không, quyết định không cho qua
class Admin(ActiveModel):
    user = models.OneToOneField(User, on_delete=models.CASCADE, primary_key=True)
    
    def email(self):
        return self.user.email
  
 #3  đã admin, đã serializer, đã API
class Landlord(InformationUserModel):
    user = models.OneToOneField(User, on_delete=models.CASCADE, primary_key=True)
    is_verified = models.BooleanField(default=False)
    slug_source = "full_name"
    def __str__(self):
        return self.full_name
    
    def email(self):
        return self.user.email
    
    class Meta:
        verbose_name = "Chủ nhà trọ"
        verbose_name_plural = "Chủ nhà trọ"

#4  đã admin, đã serializer, đã API
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

#5 đã admin, đã serializer, đã API
class Motel(SlugModel):
    id = models.AutoField(primary_key=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='motels')
    motel_name = models.CharField(max_length=255)
    slug_source = "motel_name"
    description = models.TextField()
    address = models.TextField()
    district = models.CharField(max_length=255, null = True, blank=True)
    city = models.CharField(max_length=255)
    province = models.CharField(max_length=255, null = True, blank=True)
    longitude = models.FloatField(null=True, blank=True)
    latitude = models.FloatField(null=True, blank=True)
    total_rooms = models.IntegerField()
    available_rooms = models.IntegerField()
    rating_score = models.FloatField(default=0)
    is_verified = models.BooleanField(default=False)
    
    def check_verification(self):
        if self.images.count() < 3:
            self.is_verified = False
        else:
            self.is_verified = True
        self.save()
    
    
    def __str__(self):
        return self.motel_name
    
    class Meta:
        verbose_name = "Nhà trọ"
        verbose_name_plural = "Nhà trọ"
        
 #6 đã admin, đã seralizer, đã API
class Room(SlugModel):
    id = models.AutoField(primary_key=True)
    motel = models.ForeignKey(Motel, on_delete=models.CASCADE, related_name='rooms')
    room_name = models.CharField(max_length=255)
    slug_source = "room_name"
    description = models.TextField()
    area = models.FloatField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    max_people = models.IntegerField()
    tenants = models.ManyToManyField('Tenant', through='RoomTenant', related_name='rented_rooms')
    amenities = models.ManyToManyField('Amenity')
    is_verified = models.BooleanField(default=False)
    
    
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

   
#7 đã admin
class Amenity(SlugModel):
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=255, unique=True)
    # slug = AutoSlugField(populate_from = 'name', unique=True, null = True)
    slug_source = "name"
    
    def __str__(self):
        return self.name
    
    class Meta:
        verbose_name = "Tiện nghi, tiện ích"
        verbose_name_plural = "Tiện nghi, tiện ích"

#8 đã admin
class MotelImage(BaseModel):
    id = models.AutoField(primary_key=True)
    motel = models.ForeignKey(Motel, on_delete=models.CASCADE, related_name="images")
    image_url = CloudinaryField('image')
    image_type = models.CharField(max_length=20, choices=ImageType.choices)
    
    def __str__(self):
        return f"Image for {self.motel.motel_name}"
    
    class Meta:
        verbose_name = 'hình ảnh'
        verbose_name_plural = "Hình ảnh nhà trọ"

#9  đã admin
class RoomImage(BaseModel):
    id = models.AutoField(primary_key=True)
    room = models.ForeignKey(Room, on_delete=models.CASCADE, related_name="images")
    image_url = CloudinaryField('image')
    
    def __str__(self):
        return f"Image for {self.room.room_name}"
    
    class Meta:
        verbose_name = 'hình ảnh'
        verbose_name_plural = "Hình ảnh phòng trọ"


#10 chưa biết có cho qua admin hay không
class RoomTenant(BaseModel):
    id = models.AutoField(primary_key=True)
    room = models.ForeignKey(Room, on_delete=models.CASCADE, related_name='tenant_entries')
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, related_name='room_entries')
    start_date = models.DateField()
    end_date = models.DateField()
    status = models.CharField(max_length=20, choices=RoomTenantStatus.choices)
    is_paid = models.BooleanField(default=False)

#11 chưa admin
class MotelRating(BaseModel):
    id = models.AutoField(primary_key=True)
    motel = models.ForeignKey(Motel, on_delete=models.CASCADE, related_name='ratings')
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, related_name='ratings')
    rating = models.IntegerField()
    comment = models.TextField()

    class Meta:
        verbose_name = 'Đánh giá'
        verbose_name_plural = 'Đánh giá'

#12 chưa admin
class Favorite(BaseModel):
    id = models.AutoField(primary_key=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='favorites')
    motel = models.ForeignKey(Motel, on_delete=models.CASCADE, related_name='favorited_by')

    class Meta:
        unique_together = ('user', 'motel')
        verbose_name = "Yêu thích"
        verbose_name_plural = "Yêu thích"

    def __str__(self):
        return f"{self.user.username} favorite {self.motel.motel_name}"

#13 đã admin
class Post(SlugModel):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    post_type = models.CharField(max_length=20, choices=PostType.choices)
    title = models.CharField(max_length=255)
    slug_source = "title"
    content =RichTextField()
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
 
#14 đã admin, đã serializer, đã API
class Comment(ActiveModel):
    id = models.AutoField(primary_key=True)
    post = models.ForeignKey(Post, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    content = models.TextField(blank=True, null=True)
    parent = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True,  related_name='replies')
    def __str__(self):
        return self.post.title
    
    class Meta:
        verbose_name = "Bình Luận"
        verbose_name_plural = "Bình luận"   
        
#15 đã admin
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
    

#16 đã admin
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

#17 đã admin
class SearchHistory(BaseModel):
    id = models.AutoField(primary_key=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="search_histories")
    search_params = models.JSONField()
    
    def __str__(self):
        return f"Search by {self.user.username} on {self.created_date}"
    
    def get_search_params(self):
        return json.loads(self.search_params) if isinstance(self.search_params, str) else self.search_params
    
    def set_search_params(self, params_dict):
        self.search_params = json.dumps(params_dict)
        self.save()
    
    class Meta:
        verbose_name = "Lịch sử tìm kiếm"
        verbose_name_plural = "Lịch sử tìm kiếm"
        
#18 đã admin
class Follow(BaseModel):
    id = models.AutoField(primary_key=True)
    following = models.ForeignKey(User, on_delete=models.CASCADE, related_name='following')
    followers = models.ForeignKey(User, on_delete=models.CASCADE, related_name='followers')
    last_message_time = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ('following', 'followers')
        verbose_name = "Theo dõi"
        verbose_name_plural = "Theo dõi"        

#19 đã admin
class Notifications(BaseModel):
    id = models.AutoField(primary_key=True)
    receiver = models.ForeignKey(User, on_delete=models.CASCADE)
    title = models.CharField(max_length=255)
    content = models.TextField()
    is_read = models.BooleanField(default=False)
    notification_type = models.CharField(max_length=20, choices=NotificationType.choices)
    related_object_id = models.IntegerField(null=True, blank=True)
    
    def __str__(self):
        return self.title
    

    class Meta:
        verbose_name = "Thông báo"
        verbose_name_plural = "Thông báo"  
    
#20 đã admin
class ChatRoom(BaseModel):
    id = models.AutoField(primary_key=True)
    user1 = models.ForeignKey(User, on_delete=models.CASCADE, related_name="chatrooms1")
    user2 = models.ForeignKey(User, on_delete=models.CASCADE, related_name="chatrooms2")
    
    def __str__(self):
        return f"{self.user1.username} -  {self.user2.username }"
    
#21 đã admin
class RealTimeChat(BaseModel):
    id = models.AutoField(primary_key=True)
    sender = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sent_messages')
    receiver = models.ForeignKey(User, on_delete=models.CASCADE, related_name='received_messages')
    chatroom = models.ForeignKey(ChatRoom, on_delete=models.CASCADE, related_name="messages")
    is_read = models.BooleanField(default=False)
    
    def __str__(self):
        return f"sender: {self.sender.username} - receiver: {self.receiver.username}"
    
#22 đã admin
class Payment(BaseModel):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    payer = models.ForeignKey(User, on_delete=models.CASCADE, related_name='payments')
    room = models.ForeignKey(Room, on_delete=models.CASCADE, related_name='payments')
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    payment_method = models.CharField(max_length=20, choices=PaymentMethod.choices)
    status = models.CharField(max_length=20, choices=PaymentStatus.choices)
    description = models.TextField(null = True, blank=True)
    
    class Meta:
        verbose_name = "Thanh toán"
        verbose_name_plural = "Thanh toán"