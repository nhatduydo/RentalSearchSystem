from django.contrib import admin
from django import forms
from accommodationSearch.models import User, Admin, Landlord, Tenant, Motel, Room, Amenity, RoomTenant, MotelRating, Payment, Notifications, MotelImage, RoomImage, Post, Comment, Favorite, Follow
from django.urls import path
from django.utils.safestring import mark_safe
from django.utils.html import format_html
from django.contrib.auth.models import Group



class MotelForm(forms.ModelForm):
    class Meta:
        model = Motel
        fields = '__all__'

class UserForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput(attrs={
            'id': 'password',
            'class': 'password-field',
            'style': 'padding-right: 30px;'
        }), label="Password")
    
    class Meta:
        model = User
        fields = ['username', 'password', 'groups', 'role', 'email']
#1
class UserAdmin(admin.ModelAdmin):
    list_display = ['id','username', 'role', 'email']
    search_fields = ['full_name', 'email', 'role']
    list_filter = ['role', 'created_date']
    ordering = ['id', 'created_date']
    exclude = ['user_permissions']
    form = UserForm
#2  
class LandlordForm(forms.ModelForm):
    class Meta:
        model = Landlord
        fields = '__all__'

class LandlordAdmin(admin.ModelAdmin):
    list_display = ['full_name', 'citizen_id', 'email', 'phone', 'bank_account', 'is_verified']
    search_fields = ['full_name', 'citizen_id', 'email', 'phone', 'bank_account']
    list_filter = ['is_verified', 'gender', 'date_of_birth']
    form = LandlordForm
    

    

#3    
class TenantAdmin(admin.ModelAdmin):
    list_display = ['full_name', 'citizen_id', 'email', 'phone', 'date_of_birth', 'gender', 'bank_account']
    search_fields = ['full_name', 'citizen_id', 'email', 'phone', 'bank_account']
    list_filter = ['gender', 'date_of_birth', 'active']
#4    
class MotelAdmin(admin.ModelAdmin): 
    list_display = ['id', 'motel_name','address','district','city','province','total_rooms','available_rooms', 'rating_score',  'active']
    search_fields = ['motel_name', 'address','active']
    list_filter = ['city', 'province']
    prepopulated_fields = {'slug': ('motel_name',)}
    form = MotelForm 

    @staticmethod
    def image_view(motel):
        return mark_safe(f"<img src='{motel.image.url}' width='200' />")
    

#5
class RoomAdmin(admin.ModelAdmin):
    list_display = ['room_name', 'area', 'price','max_people']
    search_fields = ['room_name', 'motel__motel_name']
    list_filter = ['motel', 'price', 'max_people']
    
    @staticmethod
    def image_view(room):
        return mark_safe(f"<img src='{room.image.url}' width='200' />")

#6
# class MotelImageAdmin(admin.ModelAdmin):
#     list_display = ['motel', 'image_preview', 'image_type'], 
    
#     def image_preview(self, obj):
#         return format_html('<img src="{}" width="50" height="50" />', obj.image_url.url)
#     image_preview.short_description = 'Preview'

# #7
# class RoomImageAdmin(admin.ModelAdmin):
#     list_display = ['room', 'image_preview']
    
#     def image_preview(self, obj):
#         return format_html('<img src="{}" width="50" height="50" />', obj.image_url.url)
#     image_preview.short_description = 'Preview'
    
#8
class PaymentAdmin(admin.ModelAdmin):
    list_display = ['payer', 'room', 'amount', 'payment_method', 'status']
    list_filter = ['payment_method', 'status']
    search_fields = ['payer__full_name', 'room__room_name']
  
class MyAdminSite(admin.AdminSite):
    site_header = 'HỆ THỐNG HỖ TRỢ TÌM KIẾM NHÀ TRỌ'
    
    class Media:
        js = ('/static/js/togglePassword.js', )
        

admin_site = MyAdminSite(name = 'accommodationSearchApp')
admin_site.register(Group)
admin_site.register(User, UserAdmin)
admin_site.register(Landlord, LandlordAdmin)
admin_site.register(Tenant, TenantAdmin)
admin_site.register(Motel, MotelAdmin)
admin_site.register(Amenity)
admin_site.register(Room, RoomAdmin)
admin_site.register(MotelImage)
admin_site.register(RoomImage) 
admin_site.register(Payment, PaymentAdmin)



