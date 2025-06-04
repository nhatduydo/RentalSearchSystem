from accommodationSearch.models import (Admin, Amenity, ChatRoom, Comment,
                                        Favorite, Follow, Landlord,
                                        LikeComment, LikeMotel, Message, Motel,
                                        MotelImage, MotelRating, Notifications,
                                        Payment, Post, Room, RoomImage,
                                        RoomTenant, SearchHistory, Tenant,
                                        User)
from allauth.socialaccount.models import SocialAccount, SocialApp, SocialToken
from django import forms
from django.contrib import admin
from django.contrib.auth.models import Group
from django.db.models import Avg, Count
from django.template.response import TemplateResponse
from django.urls import path
from django.utils.html import format_html
from django.utils.safestring import mark_safe


class UserForm(forms.ModelForm):
    """
    Form tùy chỉnh cho model User
    - Tùy chỉnh trường password với widget PasswordInput
    - Override phương thức save để mã hóa password
    """
    password = forms.CharField(widget=forms.PasswordInput(attrs={
        'id': 'password',
        'class': 'password-field',
        'style': 'padding-right: 30px;'
    }), label="Password")

    class Meta:
        model = User
        fields = '__all__'

    def save(self, commit=True):
        user = super().save(commit=False)
        if self.cleaned_data.get('password'):
            user.set_password(self.cleaned_data['password'])
        if commit:
            user.save()
        return user


class UserAdmin(admin.ModelAdmin):
    """
    Cấu hình hiển thị User trong admin interface
    - list_display: Các trường hiển thị trong danh sách
    - search_fields: Các trường có thể tìm kiếm
    - list_filter: Các trường có thể lọc
    - ordering: Sắp xếp theo id và ngày tạo
    """
    list_display = ['id', 'username', 'role', 'email', 'avatar']
    search_fields = ['full_name', 'email', 'role']
    list_filter = ['role', 'created_date']
    ordering = ['id', 'created_date']
    exclude = ['user_permissions']
    form = UserForm


class LandlordAdmin(admin.ModelAdmin):
    """
    Cấu hình hiển thị Landlord (chủ trọ) trong admin
    - Hiển thị: tên, CMND, email, số điện thoại, tài khoản ngân hàng, trạng thái xác thực
    - Tìm kiếm theo: tên, CMND, email, số điện thoại, tài khoản ngân hàng
    - Lọc theo: trạng thái xác thực, giới tính, ngày sinh
    """
    list_display = ['full_name', 'citizen_id', 'email', 'phone', 'bank_account', 'is_verified']
    search_fields = ['full_name', 'citizen_id', 'email', 'phone', 'bank_account']
    list_filter = ['is_verified', 'gender', 'date_of_birth']
    exclude = ['slug']


class RoomTenantInline(admin.TabularInline):
    """
    Hiển thị danh sách người thuê trong form phòng
    - Thêm 1 form trống mặc định
    """
    model = RoomTenant
    extra = 1


class TenantAdmin(admin.ModelAdmin):
    """
    Cấu hình hiển thị Tenant (người thuê) trong admin
    - Hiển thị thông tin cá nhân và tài khoản
    - Tìm kiếm và lọc theo các tiêu chí
    """
    list_display = ['full_name', 'citizen_id', 'email', 'phone', 'date_of_birth', 'gender', 'bank_account']
    search_fields = ['full_name', 'citizen_id', 'email', 'phone', 'bank_account']
    list_filter = ['gender', 'date_of_birth', 'active']
    exclude = ['slug']


class MotelAdmin(admin.ModelAdmin):
    """
    Cấu hình hiển thị Motel (nhà trọ) trong admin
    - Hiển thị thông tin cơ bản và hình ảnh
    - Tùy chỉnh hiển thị hình ảnh với phương thức image_view
    - Các trường readonly và excluded
    """
    list_display = ['id', 'user', 'motel_name', 'address', 'district', 'city', 'province', 'total_rooms', 'available_rooms', 'rating_score', 'active', 'is_verified', 'image_view']
    search_fields = ['motel_name', 'address', 'active',  'created_date']
    list_filter = ['city', 'province',  'created_date']
    readonly_fields = ['slug', 'rating_score', 'image_view']
    exclude = ['slug']

    def image_view(self, obj):
        """
        Hiển thị hình ảnh đầu tiên của nhà trọ
        - Lấy hình ảnh đầu tiên từ danh sách hình ảnh
        - Trả về thẻ img HTML nếu có hình ảnh
        """
        first_image = obj.images.first()
        if first_image and first_image.image_url:
            return mark_safe(f"<img src='{first_image.image_url.url}' width='300' />")
        return "No image"
    image_view.short_description = 'Motel Image'


class MotelImageAdmin(admin.ModelAdmin):
    """
    Cấu hình hiển thị MotelImage (hình ảnh nhà trọ) trong admin
    - Hiển thị thông tin hình ảnh và tên nhà trọ
    - Tìm kiếm và lọc theo các tiêu chí
    """
    list_display = ['motel_id', 'image_type', 'motel_name']
    search_fields = ['motel_id', 'image_type']
    list_filter = ['motel_id', 'image_type']

    def motel_name(self, obj):
        return obj.motel.motel_name if obj.motel else 'No name'

    motel_name.short_description = 'Tên nhà trọ'


class RoomAdmin(admin.ModelAdmin):
    """
    Cấu hình hiển thị Room (phòng) trong admin
    - Hiển thị thông tin phòng và danh sách người thuê
    - Tùy chỉnh hiển thị hình ảnh
    - Sử dụng RoomTenantInline để quản lý người thuê
    """
    list_display = ['motel', 'room_name', 'area', 'price', 'max_people', 'is_verified', 'tenant_list', 'image_view']
    search_fields = ['room_name', 'motel', 'created_date']
    list_filter = ['price', 'max_people', 'motel', 'created_date']
    readonly_fields = ['slug', 'image_view']
    exclude = ['slug']
    inlines = [RoomTenantInline]

    def tenant_list(self, obj):
        """
        Hiển thị danh sách người thuê của phòng
        - Lấy tên của tất cả người thuê
        - Kết hợp thành chuỗi phân cách bằng dấu phẩy
        """
        return ",".join([romtenant.tenant.full_name for romtenant in obj.tenant_entries.all()])

    tenant_list.short_description = "tenant"

    def image_view(self, obj):
        """
        Hiển thị hình ảnh đầu tiên của phòng
        - Lấy hình ảnh đầu tiên từ danh sách hình ảnh
        - Trả về thẻ img HTML nếu có hình ảnh
        """
        first_image = obj.images.first()
        if first_image and first_image.image_url:
            return mark_safe(f"<img src='{first_image.image_url.url}' width='100' />")
        return "No image"
    image_view.short_description = 'Room Image'


class RoomImageAdmin(admin.ModelAdmin):
    """
    Cấu hình hiển thị RoomImage (hình ảnh phòng) trong admin
    - Hiển thị thông tin hình ảnh và tên nhà trọ
    - Tìm kiếm và lọc theo ngày
    """
    list_display = ['room_id', 'image_url',  'room', 'motel_name']
    search_fields = ['updated_date', 'created_date']
    list_filter = ['updated_date', 'created_date']

    def motel_name(self, obj):
        return obj.room.motel.motel_name if obj.room and obj.room.motel else 'No motel'
    motel_name.short_description = 'motel name'


class PaymentAdmin(admin.ModelAdmin):
    """
    Cấu hình hiển thị Payment (thanh toán) trong admin
    - Theo dõi người trả, phòng, số tiền, phương thức và trạng thái
    - Tìm kiếm và lọc theo các tiêu chí
    """
    list_display = ['payer', 'room', 'amount', 'payment_method', 'status']
    list_filter = ['payment_method', 'status',  'created_date']
    search_fields = ['user', 'room',  'created_date']


class MotelRatingAdmin(admin.ModelAdmin):
    """
    Cấu hình hiển thị MotelRating (đánh giá) trong admin
    - Quản lý đánh giá và bình luận của người dùng
    - Tìm kiếm và lọc theo các tiêu chí
    """
    list_display = ['motel', 'user', 'rating', 'comment']
    search_fields = ['motel', 'user',  'created_date']
    list_filter = ['rating',  'created_date']


class FavoriteAdmin(admin.ModelAdmin):
    """
    Cấu hình hiển thị Favorite (yêu thích) trong admin
    - Hiển thị người dùng và nhà trọ được yêu thích
    """
    list_display = ['user', 'motel']


class PostAdmin(admin.ModelAdmin):
    """
    Cấu hình hiển thị Post (bài đăng) trong admin
    - Quản lý bài đăng tìm phòng và cho thuê
    - Hiển thị thông tin chi tiết về yêu cầu và vị trí
    """
    list_display = ['user_id', 'post_type', 'title', 'desired_address', 'min_price', 'max_price', 'radius_km', 'desired_latitude', 'desired_longitude', 'motel_id', 'created_date']
    search_fields = ['title', 'user',  'created_date']
    list_filter = ['post_type',  'created_date']
    exclude = ['slug']


class CommentAdmin(admin.ModelAdmin):
    """
    Cấu hình hiển thị Comment (bình luận) trong admin
    - Hiển thị thông tin người bình luận và bài đăng
    """
    list_display = ['user', 'post__post_type', 'post', 'parent']


class LikeCommentAdmin(admin.ModelAdmin):
    """
    Cấu hình hiển thị LikeComment (thích bình luận) trong admin
    - Theo dõi người dùng thích bình luận
    """
    list_display = ['user', 'comment', 'created_date']
    search_fields = ['user', 'created_date']
    list_filter = ['user', 'created_date']


class LikeMotelAdmin(admin.ModelAdmin):
    """
    Cấu hình hiển thị LikeMotel (thích nhà trọ) trong admin
    - Theo dõi người dùng thích nhà trọ
    """
    list_display = ['user', 'motel', 'created_date']
    search_fields = ['user', 'created_date']
    list_filter = ['user', 'created_date']


class SearchHistoryAdmin(admin.ModelAdmin):
    """
    Cấu hình hiển thị SearchHistory (lịch sử tìm kiếm) trong admin
    - Theo dõi lịch sử tìm kiếm của người dùng
    """
    list_display = ['id', 'user']
    search_fields = ['user']
    list_filter = ['user']


class NotificationsAdmin(admin.ModelAdmin):
    """
    Cấu hình hiển thị Notifications (thông báo) trong admin
    - Quản lý thông báo hệ thống
    - Theo dõi trạng thái đọc và loại thông báo
    """
    list_display = ['receiver', 'title', 'is_read', 'notification_type', 'related_object_id', 'created_date']
    search_fields = ['receiver', 'notification_type', 'created_date']
    list_filter = ['receiver', 'notification_type', 'created_date']


class MessageAdmin(admin.ModelAdmin):
    """
    Cấu hình hiển thị Message (tin nhắn) trong admin
    - Quản lý tin nhắn trong phòng chat
    - Theo dõi trạng thái đọc và nội dung
    """
    list_display = ['id', 'chat_room', 'sender', 'content', 'is_read', 'created_date']
    list_filter = ['is_read', 'created_date']
    search_fields = ['content', 'sender__username']


class MyAdminSite(admin.AdminSite):
    """
    Tùy chỉnh trang admin
    - Thay đổi header
    - Thêm các URL tùy chỉnh cho thống kê:
        + Số lượng nhà trọ theo quận
        + Giá trung bình phòng theo quận
        + Top nhà trọ được yêu thích
    """
    site_header = 'HỆ THỐNG HỖ TRỢ TÌM KIẾM NHÀ TRỌ'

    def get_urls(self):
        urls = [
            path('motel-count-district/', self.motel_count_district),
            path('motel-average-price/', self.room_average_price),
            path('top-favorite-motels/', self.top_favorite_motels)
        ]
        return urls + super().get_urls()

    def motel_count_district(self, request):
        """
        Thống kê số lượng nhà trọ theo quận
        - Lọc nhà trọ đang hoạt động
        - Nhóm theo quận và đếm số lượng
        """
        data = Motel.objects.filter(active=True).values('district').annotate(motel_count=Count('id')).order_by('-motel_count')
        return TemplateResponse(request, 'admin/motel_count_district.html', {
            'stats': data
        })

    def room_average_price(self, request):
        """
        Thống kê giá trung bình phòng theo quận
        - Lọc phòng đang hoạt động
        - Nhóm theo quận và tính giá trung bình
        """
        data = Room.objects.filter(active=True).values('motel__district').annotate(avg_price=Avg('price')).order_by('-avg_price')
        return TemplateResponse(request, 'admin/room_average_price.html', {
            'stats': data
        })

    def top_favorite_motels(self, request):
        """
        Thống kê top nhà trọ được yêu thích
        - Đếm số lượt thích của mỗi nhà trọ
        - Sắp xếp theo số lượt thích giảm dần
        """
        motels = Motel.objects.annotate(like_count=Count('likemotel')).filter(like_count__gt=0).order_by('-like_count')

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


# Khởi tạo admin site tùy chỉnh
admin_site = MyAdminSite(name='accommodationSearchApp')

# Đăng ký các model với admin site
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
admin_site.register(SocialApp)
admin_site.register(SocialAccount)
admin_site.register(SocialToken)
