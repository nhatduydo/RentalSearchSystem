from django.contrib import admin
from django import forms
from accommodationSearch.models import User, Admin,LikeComment, Landlord, Tenant, Motel, Room, Amenity, RoomTenant, MotelRating, Payment, Notifications, MotelImage, RoomImage, Post, Comment, Favorite, Follow
from django.urls import path
from django.utils.safestring import mark_safe
from django.utils.html import format_html
from django.contrib.auth.models import Group


class UserForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput(attrs={
            'id': 'password',
            'class': 'password-field',
            'style': 'padding-right: 30px;'
        }), label="Password")
    
    class Meta:
        model = User
        fields = ['username', 'password', 'groups', 'role', 'email']

class UserAdmin(admin.ModelAdmin):
    list_display = ['id','username', 'role', 'email']
    search_fields = ['full_name', 'email', 'role']
    list_filter = ['role', 'created_date']
    ordering = ['id', 'created_date']
    exclude = ['user_permissions']
    form = UserForm


class LandlordForm(forms.ModelForm):
    class Meta:
        model = Landlord
        fields = ['full_name', 'citizen_id', 'phone', 'bank_account', 'is_verified']

class LandlordAdmin(admin.ModelAdmin):
    list_display = ['full_name', 'citizen_id', 'email', 'phone', 'bank_account', 'is_verified']
    search_fields = ['full_name', 'citizen_id', 'email', 'phone', 'bank_account']
    list_filter = ['is_verified', 'gender', 'date_of_birth']
    form = LandlordForm

class RoomTenantInline(admin.TabularInline):
    model = RoomTenant
    extra = 1
    
class TenantAdmin(admin.ModelAdmin):
    list_display = ['full_name', 'citizen_id', 'email', 'phone', 'date_of_birth', 'gender', 'bank_account']
    search_fields = ['full_name', 'citizen_id', 'email', 'phone', 'bank_account']
    list_filter = ['gender', 'date_of_birth', 'active']
    


class MotelForm(forms.ModelForm):
    class Meta:
        model = Motel
        fields = ['id', 'motel_name','address','district','city','province','total_rooms','available_rooms', 'rating_score',  'active', 'is_verified']


class MotelAdmin(admin.ModelAdmin): 
    list_display = ['id', 'motel_name','address','district','city','province','total_rooms','available_rooms', 'rating_score',  'active', 'is_verified']
    search_fields = ['motel_name', 'address','active']
    list_filter = ['city', 'province']
    form = MotelForm 
    
    readonly_fields = ['slug']
    readonly_fields = ['rating_score']

    @staticmethod
    def image_view(motel):
        return mark_safe(f"<img src='{motel.image.url}' width='200' />")


class MotelImageAdmin(admin.ModelAdmin):
    list_display = ['motel_id', 'image_type', 'motel_name']
    search_fields = ['motel_id', 'image_type']
    list_filter =  ['motel_id', 'image_type']
    
    def motel_name(self, obj):
        return obj.motel.motel_name if obj.motel else 'No name'
    
    motel_name.short_description = 'Tên nhà trọ'
    
        
    # def image_preview(self, obj):
    #     return format_html('<img src="{}" width="50" height="50" />', obj.image_url.url)
    # image_preview.short_description = 'Preview'
  
# class RoomForm(forms.ModelForm):
#     class Meta:
#         model = Room
#         fields = ['room_name', 'area', 'price','max_people', 'is_verified']


     
class RoomAdmin(admin.ModelAdmin):
    list_display = ['motel_name','room_name', 'area', 'price','max_people', 'is_verified', 'tenant_list']
    search_fields = ['room_name', 'motel']
    list_filter = [ 'price', 'max_people', 'motel']
    
    inlines = [RoomTenantInline]
    
    
    def tenant_list(self, obj):
        return ",".join([romtenant.tenant.full_name for romtenant in obj.tenant_entries.all()])
    
    tenant_list.short_description = "tenant"
    
    def motel_name (self, obj):
        return obj.motel.motel_name if obj.motel else 'No motel'
    motel_name.short_description = 'motel name'
    s
    @staticmethod
    def image_view(room):
        return mark_safe(f"<img src='{room.image.url}' width='200' />")
    

class RoomImageAdmin(admin.ModelAdmin):
    list_display = ['room_id','image_url',  'room_name', 'motel_name']
    search_fields = ['room', 'room__motel']
    list_filter = ['room__motel', 'room']
    
    def room_name(self, obj):
        return obj.room.room_name if obj.room else 'No name'
    room_name.short_description = 'Tên phòng trọ'
    
    def motel_name (self, obj):
        return obj.room.motel.motel_name if obj.room and obj.room.motel else 'No motel'
    motel_name.short_description = 'Tên nhà trọ'
    
    # def image_preview(self, obj):
    #     return format_html('<img src="{}" width="50" height="50" />', obj.image_url.url)
    # image_preview.short_description = 'Preview'
    
#8
class PaymentAdmin(admin.ModelAdmin):
    list_display = ['payer', 'room', 'amount', 'payment_method', 'status']
    list_filter = ['payment_method', 'status']
    search_fields = ['payer__full_name', 'room__room_name']


class MotelRatingAdmin(admin.ModelAdmin):
    list_display = ['motel', 'tenant', 'rating', 'comment']
    search_fields = ['motel', 'tenant']
    list_filter = ['rating']
    
class FavoriteAdmin(admin.ModelAdmin):
    list_display = ['user', 'motel']   
    
        
class PostAdmin(admin.ModelAdmin):
    list_display = [ 'user_id', 'post_type', 'title','desired_address', 'min_price', 'max_price', 'radius_km', 'desired_latitude', 'desired_longitude', 'motel_id', 'created_date']
    search_fields = ['title', 'user']
    list_filter = ['post_type']

class CommentAdmin(admin.ModelAdmin):
    list_display = ['user', 'post__post_type', 'post', 'parent']


class LikeCommentAdmin(admin.ModelAdmin):
    list_display = ['user']

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
admin_site.register(MotelImage, MotelImageAdmin)
admin_site.register(RoomImage, RoomImageAdmin) 
admin_site.register(Payment, PaymentAdmin)
admin_site.register(MotelRating, MotelRatingAdmin)
admin_site.register(Favorite, FavoriteAdmin)
admin_site.register(Post, PostAdmin)
admin_site.register(Comment, CommentAdmin)
admin_site.register(LikeComment, LikeCommentAdmin)


