from django.db import models
from autoslug import AutoSlugField
from django.contrib.auth.models import AbstractUser
from cloudinary.models import CloudinaryField
import uuid
import json
from ckeditor.fields import RichTextField


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
    avtive = models.BooleanField(default=True)
    
    class Meta:
        abstract = True

#1
class User(AbstractUser):
    role = models.CharField(max_length=20, choices=UserRole.choices)
    full_name = models.CharField(max_length=255)
    email = models.EmailField(unique=True)
    phone = models.CharField(max_length=20, unique=True)
    avatar = CloudinaryField('avatar', blank = True, null = True)
    address = models.TextField(blank = True, null = True)
    created_date = models.DateTimeField(auto_now_add=True)
    
#2
class Admin(ActiveModel):
    user = models.OneToOneField(User, on_delete=models.CASCADE, primary_key=True)
  
 #3   
class Landlord(ActiveModel):
    user = models.OneToOneField(User, on_delete=models.CASCADE, primary_key=True)
    landlord_name = models.CharField(max_length=255)
    citizen_id = models.CharField(max_length=20, unique=True)
    bank_account = models.CharField(max_length=100)
    is_verified = models.BooleanField(default=False)

#4    
class Tenant(ActiveModel):
    user = models.OneToOneField(User, on_delete=models.CASCADE, primary_key=True)
    tenant_name = models.CharField(max_length=255)
    citizen_id = models.CharField(max_length=20, unique=True)
    bank_account = models.CharField(max_length=100)
    date_of_birth = models.DateField()
    gender = models.CharField(max_length=20, choices=Gender.choices)
    bank_account = models.CharField(max_length=100, null = True)

#5
class Motel(ActiveModel):
    id = models.AutoField(primary_key=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='motels')
    motel_name = models.CharField(max_length=255)
    slug = AutoSlugField(populate_from = 'model_name', unique=True)
    description = models.TextField()
    address = models.TextField()
    district = models.CharField(max_length=255)
    city = models.CharField(max_length=255)
    province = models.CharField(max_length=255)
    longitude = models.FloatField()
    latitude = models.FloatField()
    total_rooms = models.IntegerField()
    available_rooms = models.IntegerField()
    rating_score = models.FloatField(default=0)
    
    def __str__(self):
        return self.motel_name
 #6   
class Room(ActiveModel):
    id = models.AutoField(primary_key=True)
    model = models.ForeignKey(Motel, on_delete=models.CASCADE, related_name='rooms')
    room_name = models.CharField(max_length=255)
    description = models.TextField()
    area = models.FloatField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    max_people = models.IntegerField()
    amenities = models.JSONField()
    
    class Meta:
        unique_together = ('room_name', 'motel')
        
    def __str__(self):
        return self.room_name

class RoomTenant(BaseModel):
    room = models.ForeignKey(Room, on_delete=models.CASCADE, related_name='tenants')
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, related_name='rooms')
    start_date = models.DateField()
    end_date = models.DateField()
    status = models.CharField(max_length=20, choices=RoomTenantStatus.choices)
    is_paid = models.BooleanField(default=False)

#7
class MotelImage(BaseModel):
    id = models.AutoField(primary_key=True)
    motel = models.ForeignKey(Motel, on_delete=models.CASCADE)
    image_url = CloudinaryField('image')
    image_type = models.CharField(max_length=20, choices=ImageType.choices)

#8   
class RoomImage(BaseModel):
    id = models.AutoField(primary_key=True)
    room = models.ForeignKey(Room, on_delete=models.CASCADE)
    image_url = CloudinaryField('image')

#9  
class Post(ActiveModel):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    post_type = models.CharField(max_length=20, choices=PostType.choices)
    title = models.CharField(max_length=255)
    content =RichTextField()
    created_date = models.DateTimeField(auto_now_add=True)
    desired_address = models.TextField(blank=True, null=True)
    min_price = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    max_price = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    redius_km = models.FloatField(blank=True, null=True)
    desired_latitude = models.FloatField(blank=True, null=True)
    desired_longitude = models.FloatField(blank=True, null=True)
    motel = models.ForeignKey(Motel, on_delete=models.CASCADE, blank=True, null=True)
    
        
    def __str__(self):
        return self.title
 
#10   
class Comment(ActiveModel):
    id = models.AutoField(primary_key=True)
    post = models.ForeignKey(Post, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    content = models.TextField()
    parent = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True)
    
        
    def __str__(self):
        return self.content


#11
class LikeComment(ActiveModel):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    comment = models.ForeignKey(Comment, on_delete=models.CASCADE)
    
    class Meta:
        unique_together = ('user', 'comment')

#12
class LikeMotel(ActiveModel):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    motel = models.ForeignKey(Motel, on_delete=models.CASCADE)
    
    class Meta:
        unique_together = ('user', 'motel')

#13
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
        
#14
class Follow(BaseModel):
    follower = models.ForeignKey(User, on_delete=models.CASCADE, related_name='following')
    followed = models.ForeignKey(User, on_delete=models.CASCADE, related_name='followeds')
    
#15
class Notifications(BaseModel):
    receiver = models.ForeignKey(User, on_delete=models.CASCADE)
    title = models.CharField(max_length=255)
    content = models.TextField()
    is_Read = models.BooleanField(default=False)
    notification_type = models.CharField(max_length=20, choices=NotificationType.choices)
    related_object_id = models.IntegerField()
    
    def __str__(self):
        return self.title
#16
class ChatRoom(BaseModel):
    user1 = models.ForeignKey(User, on_delete=models.CASCADE, related_name="chatrooms1")
    user2 = models.ForeignKey(User, on_delete=models.CASCADE, related_name="chatrooms2")
    
    
#17
class RealTimeChat(BaseModel):
    senser = models.ForeignKey(User, on_delete=models.CASCADE)
    receiver = models.ForeignKey(User, on_delete=models.CASCADE)
    Chatroom = models.ForeignKey(ChatRoom, on_delete=models.CASCADE)
    is_read = models.BooleanField(default=False)
    
#18
class Payment(BaseModel):
    Payer = models.ForeignKey(User, on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    payment_method = models.CharField(max_length=20, choices=PaymentMethod.choices)
    status = models.CharField(max_length=20, choices=PaymentStatus.choices)
    room = models.ForeignKey(Room, on_delete=models.CASCADE)