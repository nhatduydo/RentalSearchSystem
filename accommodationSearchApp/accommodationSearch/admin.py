from django.contrib import admin
from django import forms
from accommodationSearch.models import User, ChatRoom, Admin, RealTimeChat, LikeComment,SearchHistory, LikeMotel, Landlord, Tenant, Motel, Room, Amenity, RoomTenant, MotelRating, Payment, Notifications, MotelImage, RoomImage, Post, Comment, Favorite, Follow
from django.urls import path
from django.db.models import Count
from django.utils.safestring import mark_safe
from django.utils.html import format_html
from django.contrib.auth.models import Group
from django.urls import path
from django.template.response import TemplateResponse
from django.db.models import Avg


class UserForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput(attrs={
            'id': 'password',
            'class': 'password-field',
            'style': 'padding-right: 30px;'
        }), label="Password")
    
    class Meta:
        model = User
        fields = '__all__'
        
class UserAdmin(admin.ModelAdmin):
    list_display = ['id','username', 'role', 'email']
    search_fields = ['full_name', 'email', 'role']
    list_filter = ['role', 'created_date']
    ordering = ['id', 'created_date']
    exclude = ['user_permissions']
    form = UserForm

class LandlordAdmin(admin.ModelAdmin):
    list_display = ['full_name', 'citizen_id', 'email', 'phone', 'bank_account', 'is_verified']
    search_fields = ['full_name', 'citizen_id', 'email', 'phone', 'bank_account']
    list_filter = ['is_verified', 'gender', 'date_of_birth']
    # form = LandlordForm

class RoomTenantInline(admin.TabularInline):
    model = RoomTenant
    extra = 1
    
class TenantAdmin(admin.ModelAdmin):
    list_display = ['full_name', 'citizen_id', 'email', 'phone', 'date_of_birth', 'gender', 'bank_account']
    search_fields = ['full_name', 'citizen_id', 'email', 'phone', 'bank_account']
    list_filter = ['gender', 'date_of_birth', 'active']
    

class MotelAdmin(admin.ModelAdmin): 
    list_display = ['id','user', 'motel_name','address','district','city','province','total_rooms','available_rooms', 'rating_score',  'active', 'is_verified']
    search_fields = ['motel_name', 'address','active',  'created_date']
    list_filter = ['city', 'province',  'created_date']
    
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
    
     
class RoomAdmin(admin.ModelAdmin):
    list_display = ['motel','room_name', 'area', 'price','max_people', 'is_verified', 'tenant_list']
    search_fields = ['room_name', 'motel', 'created_date']
    list_filter = [ 'price', 'max_people', 'motel', 'created_date']
    
    inlines = [RoomTenantInline]
    
    
    def tenant_list(self, obj):
        return ",".join([romtenant.tenant.full_name for romtenant in obj.tenant_entries.all()])
    
    tenant_list.short_description = "tenant"
    
    
    @staticmethod
    def image_view(room):
        return mark_safe(f"<img src='{room.image.url}' width='200' />")
    

class RoomImageAdmin(admin.ModelAdmin):
    list_display = ['room_id','image_url',  'room', 'motel_name']
    search_fields = ['updated_date', 'created_date']
    list_filter = [ 'updated_date', 'created_date']
    
    
    def motel_name (self, obj):
        return obj.room.motel.motel_name if obj.room and obj.room.motel else 'No motel'
    motel_name.short_description = 'motel name'
    
    # def image_preview(self, obj):
    #     return format_html('<img src="{}" width="50" height="50" />', obj.image_url.url)
    # image_preview.short_description = 'Preview'
    
#8
class PaymentAdmin(admin.ModelAdmin):
    list_display = ['payer', 'room', 'amount', 'payment_method', 'status']
    list_filter = ['payment_method', 'status',  'created_date']
    search_fields = ['user', 'room',  'created_date']


class MotelRatingAdmin(admin.ModelAdmin):
    list_display = ['motel', 'tenant', 'rating', 'comment']
    search_fields = ['motel', 'tenant',  'created_date']
    list_filter = ['rating',  'created_date']
    
class FavoriteAdmin(admin.ModelAdmin):
    list_display = ['user', 'motel']   
    
        
class PostAdmin(admin.ModelAdmin):
    list_display = [ 'user_id', 'post_type', 'title','desired_address', 'min_price', 'max_price', 'radius_km', 'desired_latitude', 'desired_longitude', 'motel_id', 'created_date']
    search_fields = ['title', 'user',  'created_date']
    list_filter = ['post_type',  'created_date']

class CommentAdmin(admin.ModelAdmin):
    list_display = ['user', 'post__post_type', 'post', 'parent']


class LikeCommentAdmin(admin.ModelAdmin):
    list_display = ['user', 'comment', 'created_date']
    search_fields = ['user', 'created_date']
    list_filter = ['user', 'created_date']
    
class LikeMotelAdmin(admin.ModelAdmin):
    list_display = ['user', 'motel', 'created_date']
    search_fields = ['user', 'created_date']
    list_filter = ['user', 'created_date']

class SearchHistoryAdmin(admin.ModelAdmin):
    list_display = ['id', 'user']
    search_fields = ['user']
    list_filter = ['user']


class NotificationsAdmin(admin.ModelAdmin):
    list_display = ['receiver', 'title', 'is_read', 'notification_type', 'related_object_id', 'created_date']
    search_fields = ['receiver', 'notification_type', 'created_date']
    list_filter = ['receiver', 'notification_type', 'created_date']


class MyAdminSite(admin.AdminSite):
    site_header = 'HỆ THỐNG HỖ TRỢ TÌM KIẾM NHÀ TRỌ'
    
    
    def get_urls(self):
        urls = [
            path('motel-count-district/', self.motel_count_district) , 
            path('motel-average-price/', self.room_average_price), 
            path('top-favorite-motels/', self.top_favorite_motels)
        ]
        return urls + super().get_urls()

    def motel_count_district(self, request):
        
        data = Motel.objects.filter(active=True).values('district').annotate(motel_count = Count('id')).order_by('-motel_count')
        return TemplateResponse(request, 'admin/motel_count_district.html', {
            'stats': data
        })
    
    
    def room_average_price(self, request):
        data = Room.objects.filter(active = True).values('motel__district').annotate(avg_price = Avg('price')).order_by('-avg_price')
        return TemplateResponse(request, 'admin/room_average_price.html', {
            'stats': data
        })
        
    def top_favorite_motels(self, request):
        
        motels = Motel.objects.annotate(like_count = Count('likemotel')).filter(like_count__gt=0).order_by('-like_count')
        
        datas = []
        for motel in motels:
            datas.append({
                'motel_name': motel.motel_name,
                'like_count': motel.like_count
            })
        return TemplateResponse(request, 'admin/top_favorite_motels.html', {
            'stats': datas
        })
        
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
admin_site.register(LikeMotel, LikeMotelAdmin)
admin_site.register(SearchHistory, SearchHistoryAdmin)
admin_site.register(Follow)
admin_site.register(Notifications, NotificationsAdmin)
admin_site.register(ChatRoom)
admin_site.register(RealTimeChat)

