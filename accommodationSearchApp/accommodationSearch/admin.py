from django.contrib import admin
from django import forms
from accommodationSearch.models import User, Admin, Landlord, Tenant, Motel, Room, Amenity, RoomTenant, MotelRating, Payment, Notifications, MotelImage, RoomImage, Post, Comment, Favorite, Follow
from django.urls import path


class MotelForm(forms.ModelForm):
    class Meta:
        model = Motel
        fields = '__all__'

class UserAdmin(admin.ModelAdmin):
    list_display = ['id', 'full_name', 'email', 'phone', 'role', 'address', 'created_date']
    search_fields = ['full_name', 'email', 'role']
    list_filter = ['role', 'created_date']
    ordering = ['id', 'created_date']
    
    
class LandlordAdmin(admin.ModelAdmin):
    list_display = ['landlord_name', 'citizen_id', 'bank_account', 'is_verified']
    search_fields = ['landlord_name', 'citizen_id', 'bank_account']
    list_filter = ['is_verified']
    
class TenantAdmin(admin.ModelAdmin):
    list_display = ['tenant_name', 'citizen_id', 'date_of_birth', 'gender', 'bank_account']
    search_fields = ['tenant_name', 'citizen_id', 'bank_account']
    list_filter = ['gender', 'date_of_birth']
    
class MotelAdmin(admin.ModelAdmin): 
    list_display = ['id', 'motel_name','address','district','city','province','total_rooms','available_rooms', 'rating_score',  'active']
    search_fields = ['motel_name', 'address','active']
    list_filter = ['city', 'province']
    prepopulated_fields = {'slug': ('motel_name',)}
    form = MotelForm 

class RoomAdmin(admin.ModelAdmin):
    list_display = ['room_name', 'area', 'price','max_people', 'amenities']

class MyAdminSite(admin.AdminSite):
    site_header = 'HỆ THỐNG HỖ TRỢ TÌM KIẾM NHÀ TRỌ'

admin_site = MyAdminSite(name = 'accommodationSearchApp')
admin_site.register(User, UserAdmin)
admin_site.register(Landlord, LandlordAdmin)
admin_site.register(Tenant, TenantAdmin)
admin_site.register(Motel, MotelAdmin)
admin_site.register(Amenity)

