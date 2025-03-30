from django.db import models
from autoslug import AutoSlugField
from django.contrib.auth.models import AbstractUser
from cloudinary.models import CloudinaryField
import uuid
import json
from ckeditor.fields import RichTextField
from django.core.exceptions import ValidationError
from django.db.models import Count
from django.utils.timezone import now


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

class InfomationUserModel(ActiveModel):
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

#1
class User(AbstractUser):
    role = models.CharField(max_length=20, choices=UserRole.choices)
    date_joined = models.DateTimeField(default=now)
    last_login = None
    created_date = models.DateTimeField(auto_now_add=True)
    updated_date = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "User"
        verbose_name_plural = "Danh sách User"
    
#2
class Admin(ActiveModel):
    user = models.OneToOneField(User, on_delete=models.CASCADE, primary_key=True)
    
    def email(self):
        return self.user.email
  
 #3   
class Landlord(InfomationUserModel):
    user = models.OneToOneField(User, on_delete=models.CASCADE, primary_key=True)
    is_verified = models.BooleanField(default=False)
    
    def __str__(self):
        return self.full_name
    
    def email(self):
        return self.user.email
    
    class Meta:
        verbose_name = "Chủ nhà trọ"
        verbose_name_plural = "Danh sách chủ trọ"

#4    
class Tenant(InfomationUserModel):
    user = models.OneToOneField(User, on_delete=models.CASCADE, primary_key=True,  related_name="tenant_profile")
    
    def __str__(self):
        return self.full_name
    
    def email(self):
        return self.user.email
    
    class Meta:
        verbose_name = "Người thuê trọ"
        verbose_name_plural = "Danh sách người thuê trọ"

#5
class Motel(ActiveModel):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='motels')
    motel_name = models.CharField(max_length=255)
    slug = AutoSlugField(populate_from = 'motel_name', unique=True)
    description = models.TextField()
    address = models.TextField()
    district = models.CharField(max_length=255)
    city = models.CharField(max_length=255)
    province = models.CharField(max_length=255)
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
        verbose_name_plural = "Danh sách nhà trọ"
 #6   
class Room(ActiveModel):
    motel = models.ForeignKey(Motel, on_delete=models.CASCADE, related_name='rooms')
    room_name = models.CharField(max_length=255)
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
        verbose_name_plural = "Danh sách phòng trọ"
        
    def __str__(self):
        return f"{self.motel.motel_name} - {self.room_name}"

   
#7   
class Amenity(BaseModel):
    name = models.CharField(max_length=255, unique=True)
    
    def __str__(self):
        return self.name
    
    class Meta:
        verbose_name = "tiện nghi, tiện ích"
        verbose_name_plural = "Danh sách các tiện ích"

#8
class MotelImage(BaseModel):
    motel = models.ForeignKey(Motel, on_delete=models.CASCADE, related_name="images")
    image_url = CloudinaryField('image')
    image_type = models.CharField(max_length=20, choices=ImageType.choices)
    
    def __str__(self):
        return f"Image for {self.motel.motel_name}"
    
    class Meta:
        verbose_name = 'hình ảnh'
        verbose_name_plural = "Danh sách hình ảnh nhà trọ"

#9  
class RoomImage(BaseModel):
    room = models.ForeignKey(Room, on_delete=models.CASCADE, related_name="images")
    image_url = CloudinaryField('image')
    
    def __str__(self):
        return f"Image for {self.room.room_name}"
    
    class Meta:
        verbose_name = 'hình ảnh'
        verbose_name_plural = "Danh sách hình ảnh phòng trọ"


#10
class RoomTenant(BaseModel):
    room = models.ForeignKey(Room, on_delete=models.CASCADE, related_name='tenant_entries')
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, related_name='room_entries')
    start_date = models.DateField()
    end_date = models.DateField()
    status = models.CharField(max_length=20, choices=RoomTenantStatus.choices)
    is_paid = models.BooleanField(default=False)

#11
class MotelRating(BaseModel):
    motel = models.ForeignKey(Motel, on_delete=models.CASCADE, related_name='ratings')
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, related_name='ratings')
    rating = models.IntegerField()
    comment = models.TextField()

#12
class Favorite(BaseModel):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='favorites')
    motel = models.ForeignKey(Motel, on_delete=models.CASCADE, related_name='favorited_by')


#13
class Post(ActiveModel):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    post_type = models.CharField(max_length=20, choices=PostType.choices)
    title = models.CharField(max_length=255)
    content =RichTextField()
    desired_address = models.TextField(blank=True, null=True)
    min_price = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    max_price = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    radius_km = models.FloatField(blank=True, null=True)
    desired_latitude = models.FloatField(blank=True, null=True)
    desired_longitude = models.FloatField(blank=True, null=True)
    motel = models.ForeignKey(Motel, on_delete=models.CASCADE, blank=True, null=True)
    
        
    def __str__(self):
        return self.title
 
#14
class Comment(ActiveModel):
    post = models.ForeignKey(Post, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    content = RichTextField()
    parent = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True)
    
        
    def __str__(self):
        return self.content


#15
class LikeComment(ActiveModel):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    comment = models.ForeignKey(Comment, on_delete=models.CASCADE)
    
    class Meta:
        unique_together = ('user', 'comment')

#16
class LikeMotel(ActiveModel):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    motel = models.ForeignKey(Motel, on_delete=models.CASCADE)
    
    class Meta:
        unique_together = ('user', 'motel')

#17
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
        
#18
class Follow(BaseModel):
    follower = models.ForeignKey(User, on_delete=models.CASCADE, related_name='following')
    followed = models.ForeignKey(User, on_delete=models.CASCADE, related_name='followers')
    last_message_time = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ('follower', 'followed')
#19
class Notifications(BaseModel):
    receiver = models.ForeignKey(User, on_delete=models.CASCADE)
    title = models.CharField(max_length=255)
    content = models.TextField()
    is_read = models.BooleanField(default=False)
    notification_type = models.CharField(max_length=20, choices=NotificationType.choices)
    related_object_id = models.IntegerField(null=True, blank=True)
    
    def __str__(self):
        return self.title
#20
class ChatRoom(BaseModel):
    user1 = models.ForeignKey(User, on_delete=models.CASCADE, related_name="chatrooms1")
    user2 = models.ForeignKey(User, on_delete=models.CASCADE, related_name="chatrooms2")
    
    
#21
class RealTimeChat(BaseModel):
    sender = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sent_messages')
    receiver = models.ForeignKey(User, on_delete=models.CASCADE, related_name='received_messages')
    chatroom = models.ForeignKey(ChatRoom, on_delete=models.CASCADE, related_name="messages")
    is_read = models.BooleanField(default=False)
    
#22
class Payment(BaseModel):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    payer = models.ForeignKey(User, on_delete=models.CASCADE, related_name='payments')
    room = models.ForeignKey(Room, on_delete=models.CASCADE, related_name='payments')
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    payment_method = models.CharField(max_length=20, choices=PaymentMethod.choices)
    status = models.CharField(max_length=20, choices=PaymentStatus.choices)
    description = models.TextField()
    
    class Meta:
        verbose_name = "Thanh toán"
        verbose_name_plural = "Danh sách thanh toán"