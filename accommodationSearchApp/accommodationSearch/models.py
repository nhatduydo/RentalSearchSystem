from django.db import models
from autoslug import AutoSlugField
from django.contrib.auth.models import AbstractUser
from cloudinary.models import CloudinaryField
import uuid
import json


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

class User(AbstractUser):
    role = models.CharField(max_length=20, choices=UserRole.choices)
    full_name = models.CharField(max_length=255)
    email = models.EmailField(unique=True)
    phone = models.CharField(max_length=20, unique=True)
    avatar = CloudinaryField('avatar', blank = True, null = True)
    address = models.TextField(blank = True, null = True)
    created_date = models.DateTimeField(auto_now_add=True)
    
class Admin(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, primary_key=True)
    
class Landlord(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, primary_key=True)
    landlord_name = models.CharField(max_length=255)
    citizen_id = models.CharField(max_length=20, unique=True)
    bank_account = models.CharField(max_length=100)
    is_verified = models.BooleanField(default=False)
    
class Tenant(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, primary_key=True)
    tenant_name = models.CharField(max_length=255)
    citizen_id = models.CharField(max_length=20, unique=True)
    bank_account = models.CharField(max_length=100)
    date_of_birth = models.DateField()
    gender = models.CharField(max_length=20, choices=Gender.choices)
    bank_account = models.CharField(max_length=100, null = True)
    
class Motel (models.Model):
    id = models.AutoField(primary_key=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
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
    status = models.BooleanField(default=True)
    rating_score = models.FloatField(default=0)
    
class Room(models.Model):
    id = models.AutoField(primary_key=True)
    model = models.ForeignKey(Motel, on_delete=models.CASCADE, related_name='rooms')
    room_name = models.CharField(max_length=255)
    description = models.TextField()
    area = models.FloatField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    max_people = models.IntegerField()
    amenities = models.TextField()
    status = models.BooleanField(default=True)
    
    class Meta:
        unique_together = ('room_name', 'motel')

class MotelImage(models.Model):
    id = models.AutoField(primary_key=True)
    motel = models.ForeignKey(Motel, on_delete=models.CASCADE)
    image_url = CloudinaryField('image')
    image_type = models.CharField(max_length=20, choices=ImageType.choices)
    
class RoomImage(models.Model):
    id = models.AutoField(primary_key=True)
    room = models.ForeignKey(Room, on_delete=models.CASCADE)
    image_url = CloudinaryField('image')
    
class Post(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    post_type = models.CharField(max_length=20, choices=PostType.choices)
    title = models.CharField(max_length=255)
    content = models.TextField()
    created_date = models.DateTimeField(auto_now_add=True)
    desired_address = models.TextField(blank=True, null=True)
    min_price = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    max_price = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    status = models.CharField(default=True)
    redius_km = models.FloatField(blank=True, null=True)
    desired_latitude = models.FloatField(blank=True, null=True)
    desired_longitude = models.FloatField(blank=True, null=True)
    motel = models.ForeignKey(Motel, on_delete=models.CASCADE, blank=True, null=True)
    
class Comment(models.Model):
    id = models.AutoField(primary_key=True)
    post = models.ForeignKey(Post, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    content = models.TextField()
    created_date = models.DateTimeField(auto_now_add=True)
    parent = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True)
    
class SearchHistory(models.Model):
    id = models.AutoField(primary_key=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="search_histories")
    search_params = models.JSONField()
    created_date = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"Search by {self.user.username} on {self.created_date}"
    
    def get_search_params(self):
        return json.loads(self.search_params) if isinstance(self.search_params, str) else self.search_params
    
    def set_search_params(self, params_dict):
        self.search_params = json.dumps(params_dict)
        self.save()