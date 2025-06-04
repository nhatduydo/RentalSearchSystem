import asyncio
import logging
import random
import string
from datetime import date, datetime, timedelta

import pytz
from allauth.socialaccount.models import SocialAccount
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from django.conf import settings
from django.contrib.auth.hashers import make_password
from django.db import transaction
from django.db.models import Avg, Count, OuterRef, Q, Subquery
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django.utils import timezone
from google.auth.transport import requests as grequests
from google.oauth2 import id_token
from oauth2_provider.models import AccessToken, Application
from rest_framework import generics, permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import (NotFound, PermissionDenied,
                                       ValidationError)
from rest_framework.permissions import AllowAny, IsAdminUser, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from . import paginators, serializers
from .email_service import EmailService
from .firebase_config import send_notification
from .models import (Amenity, ChatRoom, Comment, Favorite, Follow, Landlord,
                     LikeComment, LikeMotel, Message, Motel, MotelImage,
                     MotelRating, Notifications, NotificationType, Payment,
                     PaymentMethod, PaymentStatus, Post, PostImage, PostType,
                     Room, RoomImage, RoomTenant, RoomTenantStatus,
                     SearchHistory, Tenant, User, UserRole)
from .permissions import (IsAdmin, IsLandlordOfRoom, IsLandlordOrTenant,
                          IsOwnerOrAdmin, IsOwnerOrReadOnly,
                          IsPaymentOwnerOrMotelOwner)
from .utils import calculate_distance
from .vnpay import vnpay

logger = logging.getLogger(__name__)


def index(request):
    return HttpResponse("HỆ THỐNG HỖ TRỢ TÌM KIẾM NHÀ TRỌ")  # Trả về trang chủ với thông báo


class UserViewSet(viewsets.ViewSet,
                  generics.ListAPIView,
                  generics.RetrieveAPIView,
                  generics.CreateAPIView,
                  generics.UpdateAPIView,
                  generics.DestroyAPIView):
    """
    ViewSet quản lý thông tin người dùng
    - Cho phép xem danh sách, chi tiết, tạo mới, cập nhật và xóa người dùng
    - Có phân quyền truy cập dựa trên vai trò
    """
    queryset = User.objects.filter(is_active=True)  # Lấy danh sách người dùng đang hoạt động
    serializer_class = serializers.UserSerializer  # Serializer chuyển đổi dữ liệu
    pagination_class = paginators.ItemPanigator  # Phân trang tùy chỉnh

    def get_permissions(self):
        """
        Xác định quyền truy cập cho từng action
        - Chỉ cho phép chủ sở hữu hoặc admin cập nhật/xóa
        - Cho phép tất cả người dùng xem
        """
        if self.action in ['update', 'partial_update', 'destroy']:  # Nếu là action cập nhật/xóa
            return [IsOwnerOrAdmin()]  # Yêu cầu là chủ sở hữu hoặc admin
        return [AllowAny()]  # Cho phép tất cả người dùng xem

    @transaction.atomic  # Đảm bảo tính toàn vẹn dữ liệu
    def create(self, request, *args, **kwargs):
        """
        Tạo người dùng mới với transaction để đảm bảo tính toàn vẹn dữ liệu
        - Tạo user với thông tin cơ bản
        - Tạo profile tương ứng với vai trò (Landlord/Tenant)
        - Xử lý lỗi và rollback nếu có vấn đề
        """
        try:
            # Validate dữ liệu người dùng
            user_serializer = serializers.UserSerializer(data=request.data)
            if user_serializer.is_valid():
                user = user_serializer.save()  # Lưu user mới

                # Tạo profile data cho user
                profile_data = {
                    'user': user.id,
                    'full_name': f"{user.first_name} {user.last_name}",
                    'phone': request.data.get('phone', ''),
                    'address': request.data.get('address', ''),
                    'date_of_birth': request.data.get('date_of_birth'),
                    'gender': request.data.get('gender'),
                    'bank_account': request.data.get('bank_account', ''),
                    'citizen_id': request.data.get('citizen_id', '')
                }

                # Chọn serializer phù hợp với vai trò
                role_serializers = {
                    "LANDLORD": serializers.LandlordSerializer,
                    "TENANT": serializers.TenantSerializer
                }

                if user.role in role_serializers:
                    profile_serializer = role_serializers[user.role](data=profile_data)
                    if not profile_serializer.is_valid():
                        return Response({
                            'error': 'Dữ liệu hồ sơ không hợp lệ',
                            'details': profile_serializer.errors
                        }, status=status.HTTP_400_BAD_REQUEST)
                    profile_serializer.save()
                else:
                    raise ValidationError(f"Vai trò không hợp lệ: {user.role}")

                return Response(user_serializer.data, status=status.HTTP_201_CREATED)
            return Response({
                'error': 'Dữ liệu người dùng không hợp lệ',
                'details': user_serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            transaction.set_rollback(True)  # rollback transaction nếu có lỗi
            return Response({
                'error': 'Lỗi khi tạo người dùng',
                'details': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)

    @action(methods=['GET', 'PATCH'], url_path='current-user', detail=False, permission_classes=[permissions.IsAuthenticated])
    def get_Current_user(self, request):
        """
        API endpoint để lấy và cập nhật thông tin người dùng hiện tại
        - GET: Lấy thông tin user đang đăng nhập
        - PATCH: Cập nhật thông tin user đang đăng nhập
        """
        if request.method.__eq__("PATCH"):  # Nếu là method PATCH
            user = request.user
            for key, value in request.data.items():
                if key in ['first_name', 'last_name']:
                    setattr(user, key, value)  # Cập nhật thông tin cá nhân
                elif key == 'password':
                    user.set_password(value)  # Cập nhật mật khẩu
            user.save()

            return Response(serializers.UserSerializer(user).data)
        return Response(serializers.UserSerializer(request.user).data)

    @action(methods=['PATCH'], url_path='change-password', detail=False, permission_classes=[permissions.IsAuthenticated])
    def change_password(self, request):
        """
        API endpoint để thay đổi mật khẩu
        - Kiểm tra mật khẩu cũ
        - Xác nhận mật khẩu mới
        - Cập nhật mật khẩu mới
        """
        old_password = request.data.get("old_password")  # Lấy mật khẩu cũ
        new_password = request.data.get("new_password")  # Lấy mật khẩu mới
        confirm_password = request.data.get("confirm_password")  # Lấy xác nhận mật khẩu

        if not old_password or not new_password or not confirm_password:
            # Kiểm tra người dùng đã nhập đủ thông tin chưa
            return Response({
                "error": "Vui lòng điền đầy đủ thông tin mật khẩu cũ và mới"
            }, status=status.HTTP_400_BAD_REQUEST)

        if not request.user.check_password(old_password):
            # Kiểm tra mật khẩu cũ có đúng không
            return Response({
                "error": "Mật khẩu cũ không chính xác"
            }, status=status.HTTP_400_BAD_REQUEST)

        if new_password != confirm_password:
            # Kiểm tra xác nhận mật khẩu mới
            return Response({
                "error": "Mật khẩu mới không khớp"
            }, status=status.HTTP_400_BAD_REQUEST)

        if len(new_password) < 8:
            # Kiểm tra validate mật khẩu phải có ít nhất 8 ký tự
            return Response({
                "error": "Mật khẩu mới phải có ít nhất 8 ký tự"
            }, status=status.HTTP_400_BAD_REQUEST)

        request.user.set_password(new_password)  # Cập nhật mật khẩu mới
        request.user.save()  # Lưu lại user
        return Response({"success": "Thay đổi mật khẩu thành công"})

    def retrieve(self, request, pk=None):
        """
        Lấy thông tin chi tiết người dùng theo ID hoặc slug
        """
        if pk.isdigit():
            username = get_object_or_404(User, id=pk)  # Tìm theo ID
        else:
            username = get_object_or_404(User, slug=pk)  # Tìm theo slug

        serializers = self.get_serializer(username)
        return Response(serializers.data)


class LandlordViewSet(viewsets.ViewSet, generics.ListAPIView, generics.RetrieveAPIView, generics.UpdateAPIView):
    """
    ViewSet quản lý thông tin chủ nhà
    - Cho phép xem danh sách, chi tiết và cập nhật thông tin chủ nhà
    - Có phân quyền truy cập dựa trên vai trò
    """
    queryset = Landlord.objects.filter(active=True).order_by('user_id')  # Lấy danh sách chủ nhà đang hoạt động và sắp xếp theo ID
    serializer_class = serializers.LandlordSerializer  # Serializer chuyển đổi dữ liệu
    pagination_class = paginators.ItemPanigator  # Phân trang tùy chỉnh
    permission_classes = [AllowAny]  # Mặc định cho phép tất cả người dùng truy cập

    def get_permissions(self):
        """
        Xác định quyền truy cập cho từng action
        - Chỉ cho phép chủ sở hữu hoặc admin cập nhật
        - Cho phép tất cả người dùng xem
        """
        if self.action in ['update', 'partial_update', 'destroy']:
            return [IsOwnerOrAdmin()]
        return [AllowAny()]

    def retrieve(self, request, pk=None):
        """
        Lấy thông tin chi tiết chủ nhà theo ID, username hoặc slug
        - Tìm kiếm theo ID nếu pk là số
        - Tìm kiếm theo username hoặc slug nếu pk là chuỗi
        """
        try:
            if pk.isdigit():
                landlord = get_object_or_404(Landlord, user_id=pk)  # tìm theo ID
            else:
                # Tìm theo username hoặc slug
                landlord = get_object_or_404(Landlord, Q(user__username=pk) | Q(slug=pk))

            serializers = self.get_serializer(landlord)
            return Response(serializers.data)
        except Exception as e:
            return Response(
                {"error": f"Không tìm thấy chủ nhà với thông tin: {pk}"},
                status=status.HTTP_404_NOT_FOUND
            )

    def get_queryset(self):
        """
        Lấy danh sách chủ nhà với các điều kiện tìm kiếm
        - Lọc theo ID người dùng
        - Lọc theo tên
        - Lọc theo slug
        """
        query = self.queryset

        if self.action.__eq__('list'):
            user_id = self.request.query_params.get('id')
            if user_id:
                query = query.filter(user_id=user_id)  # lọc theo ID

            search_query = self.request.query_params.get('q')
            if search_query:
                query = query.filter(full_name__icontains=search_query)  # tìm kiếm theo tên

            slug_source = self.request.query_params.get('slug_source')
            if slug_source:
                query = query.filter(slug=slug_source)  # lọc theo slug
        return query

    def update(self, request, *args, **kwargs):
        """
        Cập nhật thông tin chủ nhà
        - Kiểm tra quyền cập nhật
        - Cập nhật thông tin nếu có quyền
        - Trả về thông báo lỗi nếu không có quyền
        """
        try:
            pk = kwargs.get('pk')
            if pk.isdigit():
                landlord = get_object_or_404(Landlord, user_id=pk)  # tìm theo ID
            else:
                # Tìm theo username hoặc slug
                landlord = get_object_or_404(Landlord, Q(user__username=pk) | Q(slug=pk))

            # Kiểm tra quyền cập nhật
            if request.user != landlord.user and not request.user.is_staff:
                return Response(
                    {'error': 'Bạn không có quyền cập nhật thông tin này'},
                    status=status.HTTP_403_FORBIDDEN
                )

            # Cập nhật thông tin
            serializer = self.get_serializer(landlord, data=request.data, partial=True)
            serializer.is_valid(raise_exception=True)  # kiểm tra dữ liệu hợp lệ
            serializer.save()

            return Response({
                'landlord': serializer.data,
                'message': 'Cập nhật thông tin thành công'
            })

        except Exception as e:
            logger.error(f"Lỗi khi cập nhật chủ nhà: {str(e)}")
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )

    @action(methods=['PATCH'], detail=True, url_path='verify')
    def verify(self, request, pk=None):
        """
        Xác thực chủ nhà (chỉ admin mới có quyền)
        - Kiểm tra quyền xác thực
        - Cập nhật trạng thái xác thực
        - Tạo thông báo cho chủ nhà
        """
        try:
            if pk.isdigit():
                landlord = get_object_or_404(Landlord, user_id=pk)  # tìm theo ID
            else:
                # Tìm theo username hoặc slug
                landlord = get_object_or_404(Landlord, Q(user__username=pk) | Q(slug=pk))

            # Kiểm tra quyền xác thực
            if not request.user.is_staff:
                return Response(
                    {'error': 'Chỉ admin mới có quyền xác thực chủ nhà'},
                    status=status.HTTP_403_FORBIDDEN
                )

            landlord.is_verified = True  # cập nhật trạng thái xác thực
            landlord.save()

            # Tạo thông báo cho chủ nhà
            Notifications.objects.create(
                receiver=landlord.user,
                title="Tài khoản đã được xác thực",
                content="Tài khoản chủ nhà của bạn đã được xác thực thành công",
                notification_type=NotificationType.VERIFICATION_SUCCESS,
                related_object_id=landlord.user.id
            )

            # Gửi thông báo đến Firebase
            notification = Notifications.objects.latest('created_date')  # lấy notification vừa tạo
            notification_data = {
                'id': notification.id,
                'title': notification.title,
                'content': notification.content,
                'notification_type': notification.notification_type,
                'created_date': notification.created_date.isoformat(),
                'is_read': notification.is_read
            }
            send_notification(notification.receiver.id, notification_data)

            return Response({
                'landlord': self.get_serializer(landlord).data,
                'message': 'Xác thực chủ nhà thành công'
            })

        except Exception as e:
            logger.error(f"Lỗi khi xác minh chủ nhà: {str(e)}")
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )


class TenantViewSet(viewsets.ViewSet, generics.ListAPIView, generics.RetrieveAPIView, generics.UpdateAPIView):
    """
    ViewSet quản lý thông tin người thuê
    - Cho phép xem danh sách, chi tiết và cập nhật thông tin người thuê
    - Có phân quyền truy cập dựa trên vai trò
    """
    queryset = Tenant.objects.filter(active=True)  # Lấy danh sách người thuê đang hoạt động
    serializer_class = serializers.TenantSerializer  # Serializer chuyển đổi dữ liệu
    pagination_class = paginators.ItemPanigator  # Phân trang tùy chỉnh
    permission_classes = [AllowAny]  # Mặc định cho phép tất cả người dùng truy cập

    def get_permissions(self):
        """
        Xác định quyền truy cập cho từng action
        - Chỉ cho phép chủ sở hữu hoặc admin cập nhật
        - Cho phép tất cả người dùng xem
        """
        if self.action in ['update', 'partial_update', 'destroy']:  # Nếu là action cập nhật/xóa
            return [IsOwnerOrAdmin()]  # Yêu cầu là chủ sở hữu hoặc admin
        return [AllowAny()]  # Cho phép tất cả người dùng xem

    def retrieve(self, request, pk=None):
        """
        Lấy thông tin chi tiết người thuê theo ID, username hoặc slug
        - Tìm kiếm theo ID nếu pk là số
        - Tìm kiếm theo username hoặc slug nếu pk là chuỗi
        """
        try:
            if pk.isdigit():
                tenant = get_object_or_404(Tenant, user_id=pk)  # Tìm theo ID
            else:
                # Tìm theo username hoặc slug
                tenant = get_object_or_404(Tenant, Q(user__username=pk) | Q(slug=pk))

            serializers = self.get_serializer(tenant)
            return Response(serializers.data)
        except Exception as e:
            return Response(
                {"error": f"Không tìm thấy người thuê với thông tin: {pk}"},
                status=status.HTTP_404_NOT_FOUND
            )

    def get_queryset(self):
        """
        Lấy danh sách người thuê với các điều kiện tìm kiếm
        - Lọc theo ID người dùng
        - Lọc theo tên
        - Lọc theo slug
        """
        query = self.queryset

        if self.action.__eq__('list'):
            user_id = self.request.query_params.get('id')
            if user_id:
                query = query.filter(user_id=user_id)  # Lọc theo ID

            search_query = self.request.query_params.get('q')
            if search_query:
                query = query.filter(full_name__icontains=search_query)  # Tìm kiếm theo tên

            slug_source = self.request.query_params.get('slug_source')
            if slug_source:
                query = query.filter(slug=slug_source)

            # Lọc theo giới tính
            gender = self.request.query_params.get('gender')
            if gender:
                query = query.filter(gender=gender)

            # Lọc theo khoảng tuổi
            min_age = self.request.query_params.get('min_age')
            max_age = self.request.query_params.get('max_age')
            if min_age or max_age:
                today = date.today()
                if min_age:
                    max_date = today.replace(year=today.year - int(min_age))
                    query = query.filter(date_of_birth__lte=max_date)
                if max_age:
                    min_date = today.replace(year=today.year - int(max_age) - 1)  # trừ 1 vì để tính chưa tới sinh nhật thứ 25, hay 25 tuổi mấy ngày không lấy
                    query = query.filter(date_of_birth__gt=min_date)
        return query

    def update(self, request, *args, **kwargs):
        """
        Cập nhật thông tin người thuê
        - Kiểm tra quyền cập nhật
        - Cập nhật thông tin nếu có quyền
        - Trả về thông báo lỗi nếu không có quyền
        """
        try:
            pk = kwargs.get('pk')
            if pk.isdigit():
                tenant = get_object_or_404(Tenant, user_id=pk)  # Tìm theo ID
            else:
                # Tìm theo username hoặc slug
                tenant = get_object_or_404(Tenant, Q(user__username=pk) | Q(slug=pk))

            # Nếu người đang gửi yêu cầu không phải là chủ tài khoản và cũng không phải là admin không được phép cập nhật.
            if request.user != tenant.user and not request.user.is_staff:
                return Response(
                    {'error': 'Bạn không có quyền cập nhật thông tin này'},
                    status=status.HTTP_403_FORBIDDEN
                )

            # Cập nhật thông tin
            serializer = self.get_serializer(tenant, data=request.data, partial=True)
            serializer.is_valid(raise_exception=True)  # Giúp kiểm tra dữ liệu đầu vào và dừng lại ngay nếu có lỗi, không cần viết thêm code xử lý lỗi thủ công.
            serializer.save()

            return Response({
                'tenant': serializer.data,
                'message': 'Cập nhật thông tin thành công'
            })

        except Exception as e:
            logger.error(f"Lỗi khi cập nhật người thuê: {str(e)}")
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )

    @action(detail=True, methods=['get'], url_path='rooms')
    def get_rented_rooms(self, request, pk=None):
        """
        Lấy danh sách phòng đã thuê của người thuê
        - Tìm kiếm theo ID hoặc username/slug
        - Trả về danh sách phòng đang thuê
        """
        try:
            if pk.isdigit():
                tenant = get_object_or_404(Tenant, user_id=pk)
            else:
                tenant = get_object_or_404(Tenant, Q(user__username=pk) | Q(slug=pk))

            room_tenants = RoomTenant.objects.filter(
                tenant=tenant,
                active=True
            ).select_related('room', 'room__motel')
            # 'room': lấy luôn thông tin của phòng (Room) gắn với RoomTenant.
            # 'room__motel': lấy luôn thông tin nhà trọ (Motel) chứa phòng đó.
            # bạn tối ưu hóa hiệu năng bằng cách dùng JOIN trong SQL để lấy dữ liệu liên kết trong 1 truy vấn duy nhất.
            serializer = serializers.RoomTenantSerializer(room_tenants, many=True)
            return Response(serializer.data)
        except Exception as e:
            logger.error(f"Lỗi khi thuê phòng: {str(e)}")
            return Response(
                {"error": f"Không tìm thấy người thuê với thông tin: {pk}"},
                status=status.HTTP_404_NOT_FOUND
            )

    @action(detail=True, methods=['get'], url_path='payments')
    def get_payment_history(self, request, pk=None):
        """
        Lấy lịch sử thanh toán của người thuê
        - Tìm kiếm theo ID hoặc username/slug
        - Trả về danh sách các khoản thanh toán
        """
        try:
            if pk.isdigit():
                tenant = get_object_or_404(Tenant, user_id=pk)
            else:
                tenant = get_object_or_404(Tenant, Q(user__username=pk) | Q(slug=pk))

                # lọc các thanh toán do người dùng đó thực hiện.
                #  JOIN luôn bảng Room để tối ưu truy vấn
                payments = Payment.objects.filter(
                    payer=tenant.user,
                    active=True
                ).select_related('room')

            serializer = serializers.PaymentSerializer(payments, many=True)
            return Response(serializer.data)
        except Exception as e:
            logger.error(f"Lỗi khi lấy lịch sử thanh toán: {str(e)}")
            return Response(
                {"error": f"Không tìm thấy người thuê với thông tin: {pk}"},
                status=status.HTTP_404_NOT_FOUND
            )


class MotelViewSet(viewsets.ViewSet, generics.ListCreateAPIView, generics.RetrieveUpdateDestroyAPIView):
    """
    ViewSet quản lý thông tin nhà trọ
    - Cho phép xem danh sách, chi tiết, tạo mới, cập nhật và xóa nhà trọ
    - Có phân quyền truy cập dựa trên vai trò
    - Tự động gửi thông báo cho người theo dõi khi có cập nhật
    """
    queryset = Motel.objects.filter(active=True)
    serializer_class = serializers.MotelSerializer
    pagination_class = paginators.ItemPanigator

    def get_permissions(self):
        """
        Xác định quyền truy cập cho từng action
        - Chỉ cho phép chủ sở hữu hoặc admin cập nhật/xóa
        - Yêu cầu đăng nhập để tạo mới
        - Chỉ admin mới có quyền xác thực
        - Cho phép tất cả người dùng xem
        """
        if self.action in ['update', 'partial_update', 'destroy']:
            return [IsOwnerOrAdmin()]
        if self.action == 'create':
            return [IsAuthenticated()]
        if self.action == 'verify':
            return [IsAdminUser()]
        return [AllowAny()]

    @transaction.atomic
    def perform_create(self, serializer):
        """
        Tạo nhà trọ mới với transaction để đảm bảo tính toàn vẹn dữ liệu
        - Lưu thông tin nhà trọ
        - Gửi thông báo cho người theo dõi
        - Gửi email thông báo
        """
        motel = serializer.save(user=self.request.user)

        # lây danh sách người theo giỏi
        followers = self.request.user.followers.filter(active=True)
        print(f"Số người theo dõi: {followers.count()}")

        # với mỗi người theo giỏi, gửi thông báo về
        for follower in followers:
            print(f"Đang gửi thông báo cho: {follower.follower_user.email}")
            # Tạo thông báo trong database
            Notifications.objects.create(
                receiver=follower.follower_user,
                title="Nhà trọ mới",
                content=f"{self.request.user.username} vừa đăng một nhà trọ mới: {motel.motel_name}",
                notification_type=NotificationType.MOTEL_UPDATE,
                related_object_id=motel.id
            )

            # Gửi email thông báo
            try:
                email_data = {
                    'name': follower.follower_user.username,
                    'title': motel.motel_name,
                    'address': motel.address,
                    'district': motel.district,
                    'city': motel.city,
                    'province': motel.province,
                    'description': motel.description,
                    'total_rooms': motel.total_rooms,
                    'available_rooms': motel.available_rooms,
                    'latitude': motel.latitude,
                    'longitude': motel.longitude
                }

                # Gửi email bất đồng bộ sử dụng asyncio.run()
                asyncio.run(
                    EmailService.send_notification(
                        to_email=follower.follower_user.email,
                        data=email_data,
                        notification_type=NotificationType.NEW_MOTEL
                    )
                )
                print(f"Đã gửi email thông báo đến: {follower.follower_user.email}")
            except Exception as e:
                print(f"Lỗi khi gửi email đến {follower.follower_user.email}: {str(e)}")

    @transaction.atomic
    def perform_update(self, serializer):
        """
        Cập nhật thông tin nhà trọ
        - Lưu thông tin cập nhật
        - Gửi thông báo cho người theo dõi
        - Gửi email thông báo
        """
        motel = serializer.save()
        # Notify followers about the update
        followers = self.request.user.followers.filter(active=True)
        print(f"Số người theo dõi: {followers.count()}")

        for follow in followers:
            print(f"Đang gửi thông báo cập nhật cho: {follow.follower_user.email}")
            Notifications.objects.create(
                receiver=follow.follower_user,
                title="Cập nhật nhà trọ",
                content=f"{self.request.user.username} vừa cập nhật thông tin nhà trọ: {motel.motel_name}",
                notification_type=NotificationType.MOTEL_UPDATE,
                related_object_id=motel.id
            )

            try:
                email_data = {
                    'name': follow.follower_user.username,
                    'title': motel.motel_name,
                    'address': motel.address,
                    'district': motel.district,
                    'city': motel.city,
                    'province': motel.province,
                    'description': motel.description,
                    'total_rooms': motel.total_rooms,
                    'available_rooms': motel.available_rooms,
                    'latitude': motel.latitude,
                    'longitude': motel.longitude
                }

                # Gửi email bất đồng bộ sử dụng asyncio.run()
                asyncio.run(
                    EmailService.send_notification(
                        to_email=follow.follower_user.email,
                        data=email_data,
                        notification_type=NotificationType.MOTEL_UPDATE
                    )
                )
                print(f"Đã gửi email thông báo cập nhật đến: {follow.follower_user.email}")
            except Exception as e:
                print(f"Lỗi khi gửi email cập nhật đến {follow.follower_user.email}: {str(e)}")

    def retrieve(self, request, pk=None):
        """
        Lấy thông tin chi tiết nhà trọ theo ID hoặc slug
        """
        if pk.isdigit():
            motel = get_object_or_404(Motel, id=pk)
        else:
            motel = get_object_or_404(Motel, slug=pk)

        serializers = self.get_serializer(motel)
        return Response(serializers.data)

    @action(methods=['POST'], detail=True, url_path='like')
    def like_motel(self, request, pk):
        """
        Like (thích) một nhà trọ
        - Tạo hoặc cập nhật trạng thái like
        - Gửi thông báo cho chủ nhà khi có người like
        """
        motel = self.get_object()
        like, created = LikeMotel.objects.get_or_create(user=request.user, motel=motel)
        if not created:
            like.active = not like.active
        like.save()

        # Thông báo cho chủ nhà khi có người like nhà trọ
        if like.active:
            Notifications.objects.create(
                receiver=motel.user,
                title="Nhà trọ được yêu thích",
                content=f"{request.user.username} đã thích nhà trọ {motel.motel_name} của bạn",
                notification_type=NotificationType.MOTEL_LIKE,
                related_object_id=motel.id
            )

            # Gửi thông báo đến Firebase
            notification = Notifications.objects.latest('created_date')  # Lấy notification vừa tạo
            notification_data = {
                'id': notification.id,
                'title': notification.title,
                'content': notification.content,
                'notification_type': notification.notification_type,
                'created_date': notification.created_date.isoformat(),
                'is_read': notification.is_read
            }
            send_notification(notification.receiver.id, notification_data)

        return Response(serializers.MotelSerializer(motel, context={'request': request}).data)

    @action(methods=['POST'], detail=True, url_path='favorite')
    def favorite_motel(self, request, pk):
        """
        Thêm nhà trọ vào danh sách yêu thích
        - Tạo hoặc cập nhật trạng thái yêu thích
        - Gửi thông báo cho chủ nhà khi có người thêm vào yêu thích
        """
        motel = self.get_object()
        favorite, created = Favorite.objects.get_or_create(user=request.user, motel=motel)
        if not created:
            favorite.active = not favorite.active
        favorite.save()

        # Thông báo cho chủ nhà khi có người thêm yêu thích
        if favorite.active:
            Notifications.objects.create(
                receiver=motel.user,
                title="Nhà trọ được yêu thích",
                content=f"{request.user.username} đã thêm nhà trọ {motel.motel_name} vào danh sách yêu thích",
                notification_type=NotificationType.MOTEL_LIKE,
                related_object_id=motel.id
            )

            # Gửi thông báo đến Firebase
            notification = Notifications.objects.latest('created_date')  # Lấy notification vừa tạo
            notification_data = {
                'id': notification.id,
                'title': notification.title,
                'content': notification.content,
                'notification_type': notification.notification_type,
                'created_date': notification.created_date.isoformat(),
                'is_read': notification.is_read
            }
            send_notification(notification.receiver.id, notification_data)

        return Response(serializers.MotelSerializer(motel, context={'request': request}).data)

    @action(methods=['PATCH'], detail=True, url_path='verify')
    def verify(self, request, pk=None):
        """
        Xác thực nhà trọ (chỉ admin mới có quyền)
        - Kiểm tra điều kiện xác thực
        - Cập nhật trạng thái xác thực
        - Gửi thông báo cho chủ nhà
        """
        if request.user.role != UserRole.ADMIN:
            return Response({
                'error': 'Chỉ admin mới có quyền xác minh nhà trọ'
            }, status=status.HTTP_403_FORBIDDEN)

        try:
            if pk.isdigit():
                motel = get_object_or_404(Motel, id=pk)
            else:
                motel = get_object_or_404(Motel, slug=pk)

            if not motel.check_verification():
                return Response({
                    'error': 'Nhà trọ chưa đủ điều kiện để xác minh. Cần có ít nhất 3 hình ảnh và địa chỉ đầy đủ'
                }, status=status.HTTP_400_BAD_REQUEST)

            # Xét duyệt nhà trọ
            motel.is_verified = True
            motel.save()

            Notifications.objects.create(
                receiver=motel.user,
                title="Nhà trọ đã được xét duyệt",
                content=f"Nhà trọ {motel.motel_name} của bạn đã được xét duyệt thành công",
                notification_type=NotificationType.VERIFICATION_SUCCESS,
                related_object_id=motel.id
            )

            # Gửi thông báo đến Firebase
            notification = Notifications.objects.latest('created_date')  # Lấy notification vừa tạo
            notification_data = {
                'id': notification.id,
                'title': notification.title,
                'content': notification.content,
                'notification_type': notification.notification_type,
                'created_date': notification.created_date.isoformat(),
                'is_read': notification.is_read
            }
            send_notification(notification.receiver.id, notification_data)

            return Response({
                'motel': self.get_serializer(motel).data,
                'message': 'Xét duyệt nhà trọ thành công'
            })

        except Exception as e:
            logger.error(f"Lỗi khi xét duyệt nhà trọ: {str(e)}")
            return Response(
                {'error': 'Có lỗi xảy ra khi xét duyệt nhà trọ'},
                status=status.HTTP_400_BAD_REQUEST
            )


class RoomViewSet(viewsets.ViewSet, generics.ListCreateAPIView, generics.RetrieveUpdateDestroyAPIView):
    """
    ViewSet quản lý thông tin phòng trọ
    - Cho phép xem danh sách, chi tiết, tạo mới, cập nhật và xóa phòng trọ
    - Có phân quyền truy cập dựa trên vai trò
    """
    queryset = Room.objects.filter(active=True)
    serializer_class = serializers.RoomSerializer
    pagination_class = paginators.ItemPanigator

    def get_permissions(self):
        """
        Xác định quyền truy cập cho từng action
        - Chỉ cho phép chủ sở hữu hoặc admin tạo mới/cập nhật/xóa
        - Cho phép tất cả người dùng xem
        """
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [IsOwnerOrAdmin()]
        return [AllowAny()]

    def retrieve(self, request, pk=None):
        """
        Lấy thông tin chi tiết phòng trọ theo ID hoặc slug
        - Tìm kiếm theo ID nếu pk là số
        - Tìm kiếm theo slug nếu pk là chuỗi
        """
        if pk.isdigit():
            room = get_object_or_404(Room, id=pk)
        else:
            room = get_object_or_404(Room, slug=pk)
        serializer = self.get_serializer(room)
        return Response(serializer.data)

    def get_queryset(self):
        """
        Lấy danh sách phòng trọ với các điều kiện tìm kiếm
        - Lọc theo nhà trọ (ID hoặc slug)
        - Lọc theo tên phòng
        - Lọc theo khoảng giá
        - Lọc theo diện tích
        - Lọc theo số người tối đa
        """
        query = self.queryset
        if self.action == 'list':
            motel_identifier = self.request.query_params.get('motel_id')
            if motel_identifier:
                if motel_identifier.isdigit():
                    query = query.filter(motel_id=motel_identifier)
                else:
                    query = query.filter(motel__slug=motel_identifier)

            filters = {}
            room_name = self.request.query_params.get('room_name')
            if room_name:
                filters['room_name__icontains'] = room_name
            min_price = self.request.query_params.get('min_price')
            if min_price:
                filters['price__gte'] = min_price
            max_price = self.request.query_params.get('max_price')
            if max_price:
                filters['price__lte'] = max_price
            min_area = self.request.query_params.get('min_area')
            if min_area:
                filters['area__gte'] = min_area
            max_area = self.request.query_params.get('max_area')
            if max_area:
                filters['area__lte'] = max_area
            max_people = self.request.query_params.get('max_people')
            if max_people:
                filters['max_people__gte'] = max_people
            if filters:
                query = query.filter(**filters)  # truyền các điều kiện lọc vào hàm filter() bằng cách giải nén dict (**filters) thành các tham số keyword.
        return query


class AmenityViewSet(viewsets.ModelViewSet):
    """
    ViewSet quản lý thông tin tiện nghi
    - Cho phép xem danh sách, chi tiết, tạo mới, cập nhật và xóa tiện nghi
    - Có phân quyền truy cập dựa trên vai trò
    """
    queryset = Amenity.objects.filter(active=True)
    serializer_class = serializers.AmenitySerializer

    def get_permissions(self):
        """
        Xác định quyền truy cập cho từng action
        - Chỉ cho phép chủ sở hữu hoặc admin tạo mới/cập nhật/xóa
        - Cho phép tất cả người dùng xem
        """
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [IsOwnerOrAdmin()]
        return [AllowAny()]

    def perform_destroy(self, instance):
        """
        Xóa mềm tiện nghi (chỉ cập nhật trạng thái active=False)
        """
        instance.active = False
        instance.save()


class MotelImageViewSet(viewsets.ModelViewSet):
    """
    ViewSet quản lý hình ảnh nhà trọ
    - Cho phép xem danh sách, chi tiết, tạo mới, cập nhật và xóa hình ảnh
    - Yêu cầu đăng nhập để thực hiện các thao tác
    """
    serializer_class = serializers.MotelImageSerializer
    permission_classes = [permissions.IsAuthenticated]
    queryset = MotelImage.objects.filter(active=True)

    def get_queryset(self):
        """
        Lấy danh sách hình ảnh với điều kiện lọc
        - Lọc theo ID nhà trọ nếu được cung cấp
        """
        queryset = MotelImage.objects.filter(active=True)
        motel_id = self.request.query_params.get('motel_id', None)
        if motel_id is not None:
            queryset = queryset.filter(motel_id=motel_id)
        return queryset

    def create(self, request, *args, **kwargs):
        motel_id = request.data.get('motel')
        if not motel_id:
            return Response({"error": "Cần ID nhà trọ"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            motel = Motel.objects.get(pk=motel_id)
            if motel.user != request.user:
                return Response({"error": "Không có quyền"}, status=status.HTTP_403_FORBIDDEN)
        except Motel.DoesNotExist:
            return Response({"error": "Không tìm thấy nhà trọ"}, status=status.HTTP_404_NOT_FOUND)

        images = request.FILES.getlist('image_url')
        if not images:
            return Response({"error": "Chưa chọn ảnh"}, status=status.HTTP_400_BAD_REQUEST)

        created_images = []
        for image in images:
            motel_image = MotelImage.objects.create(
                motel=motel,
                image_url=image,
                image_type=request.data.get('image_type', 'INSIDE')
            )
            created_images.append(motel_image)

        serializer = self.get_serializer(created_images, many=True)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def perform_destroy(self, instance):
        instance.active = False
        instance.save()


class RoomImageViewSet(viewsets.ModelViewSet):
    """
    ViewSet quản lý hình ảnh phòng trọ
    - Cho phép xem danh sách, chi tiết, tạo mới, cập nhật và xóa hình ảnh
    - Yêu cầu đăng nhập để thực hiện các thao tác
    """
    queryset = RoomImage.objects.filter(active=True)
    serializer_class = serializers.RoomImageSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_permissions(self):
        """
        Xác định quyền truy cập cho từng action
        - Chỉ cho phép chủ sở hữu hoặc admin tạo mới/cập nhật/xóa
        - Cho phép tất cả người dùng xem
        """
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [IsOwnerOrAdmin()]
        return [permissions.AllowAny()]

    def get_queryset(self):
        """
        Lấy danh sách hình ảnh với điều kiện lọc
        - Lọc theo ID phòng nếu được cung cấp
        """
        queryset = RoomImage.objects.filter(active=True)
        room_id = self.request.query_params.get('room_id', None)
        if room_id is not None:
            queryset = queryset.filter(room_id=room_id)
        return queryset

    def create(self, request, *args, **kwargs):
        """
        Tạo mới hình ảnh cho phòng trọ
        - Kiểm tra quyền sở hữu phòng
        - Tạo nhiều hình ảnh cùng lúc
        - Trả về danh sách hình ảnh đã tạo
        """
        room_id = request.data.get('room')
        if not room_id:
            return Response({'error': 'Cần ID phòng'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            room = Room.objects.get(id=room_id)
            if request.user != room.motel.user and not request.user.is_staff:
                return Response({'error': 'Không có quyền'}, status=status.HTTP_403_FORBIDDEN)

            images = request.FILES.getlist('image_url')
            if not images:
                return Response({'error': 'Chưa chọn ảnh'}, status=status.HTTP_400_BAD_REQUEST)

            created_images = []
            for image in images:
                room_image = RoomImage.objects.create(
                    room=room,
                    image_url=image
                )
                created_images.append(room_image)

            serializer = self.get_serializer(created_images, many=True)
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        except Room.DoesNotExist:
            return Response({'error': 'Không tìm thấy phòng'}, status=status.HTTP_404_NOT_FOUND)

    def perform_destroy(self, instance):
        """
        Xóa mềm hình ảnh (chỉ cập nhật trạng thái active=False)
        """
        instance.active = False
        instance.save()


class RoomTenantViewSet(viewsets.ModelViewSet):
    """
    ViewSet quản lý thông tin thuê phòng
    - Cho phép xem danh sách, chi tiết, tạo mới, cập nhật và xóa thông tin thuê phòng
    - Có phân quyền truy cập dựa trên vai trò
    """
    serializer_class = serializers.RoomTenantSerializer
    permission_classes = [IsAuthenticated]

    def get_permissions(self):
        """
        Xác định quyền truy cập cho từng action
        - Chỉ chủ trọ mới được accept/reject yêu cầu
        - Admin, chủ trọ hoặc người thuê mới được hủy hợp đồng
        - Yêu cầu đăng nhập cho các thao tác khác
        """
        if self.action in ['accept_request', 'reject_request']:
            return [IsLandlordOfRoom()]  # Chỉ chủ trọ mới được accept/reject
        elif self.action == 'cancel_contract':
            # Cho phép admin, chủ trọ hoặc người thuê cancel contract
            if self.request.user.role == UserRole.ADMIN:
                return [IsAdmin()]
            return [IsLandlordOrTenant()]
        return [IsAuthenticated()]

    #  tránh thực hiện truy vấn cơ sở dữ liệu không cần thiết khi Swagger đang tạo tài liệu (fake request).
    def get_queryset(self):
        """
        Lấy danh sách thông tin thuê phòng dựa trên vai trò
        - Admin: xem tất cả
        - Chủ trọ: xem thông tin thuê phòng trong nhà trọ của mình
        - Người thuê: chỉ xem thông tin thuê phòng của mình
        """
        if getattr(self, 'swagger_fake_view', False):
            return RoomTenant.objects.none()

        user = self.request.user
        queryset = RoomTenant.objects.select_related(
            'room__motel__user',  # Lấy thông tin user của motel
            'tenant__user'        # Lấy thông tin user của tenant
        )

        if user.role == UserRole.ADMIN:
            return queryset  # Admin được xem tất cả dữ liệu
        elif user.role == UserRole.LANDLORD:
            return queryset.filter(room__motel__user=user)  # Chủ trọ chỉ xem được dữ liệu liên quan đến các phòng trong nhà trọ của mình
        elif user.role == UserRole.TENANT:
            return queryset.filter(tenant__user=user)  # Người thuê chỉ được xem dữ liệu liên quan đến chính họ
        return RoomTenant.objects.none()

    def perform_create(self, serializer):
        """
        Tạo mới yêu cầu thuê phòng
        - Tạo thông báo cho chủ trọ
        - Gửi thông báo qua Firebase
        """
        tenant = Tenant.objects.get(user=self.request.user)
        room_tenant = serializer.save(tenant=tenant, status=RoomTenantStatus.PENDING)
        Notifications.objects.create(
            receiver=room_tenant.room.motel.user,
            title="Yêu cầu thuê phòng",
            content=f"Có yêu cầu thuê phòng mới từ {tenant.full_name}",
            notification_type=NotificationType.SYSTEM,
            related_object_id=str(room_tenant.id)
        )

        # Gửi thông báo đến Firebase
        notification = Notifications.objects.latest('created_date')  # Lấy notification vừa tạo
        notification_data = {
            'id': notification.id,
            'title': notification.title,
            'content': notification.content,
            'notification_type': notification.notification_type,
            'created_date': notification.created_date.isoformat(),
            'is_read': notification.is_read
        }
        send_notification(notification.receiver.id, notification_data)

    @action(detail=True, methods=['post'], url_path='accept-request')
    def accept_request(self, request, pk=None):
        """
        Chấp nhận yêu cầu thuê phòng
        - Chỉ chấp nhận yêu cầu đang ở trạng thái PENDING
        - Tạo thông báo cho người thuê
        - Gửi thông báo qua Firebase
        """
        room_tenant = self.get_object()
        if room_tenant.status != RoomTenantStatus.PENDING:
            return Response({"error": "Chỉ có thể chấp nhận yêu cầu đang ở trạng thái PENDING"},
                            status=status.HTTP_400_BAD_REQUEST)

        room_tenant.status = RoomTenantStatus.ACTIVE
        room_tenant.save()

        Notifications.objects.create(
            receiver=room_tenant.tenant.user,
            title="Yêu cầu được chấp nhận",
            content="Yêu cầu thuê phòng của bạn đã được chấp nhận",
            notification_type=NotificationType.SYSTEM,
            related_object_id=str(room_tenant.id)
        )

        # Gửi thông báo đến Firebase
        notification = Notifications.objects.latest('created_date')  # Lấy notification vừa tạo
        notification_data = {
            'id': notification.id,
            'title': notification.title,
            'content': notification.content,
            'notification_type': notification.notification_type,
            'created_date': notification.created_date.isoformat(),
            'is_read': notification.is_read
        }
        send_notification(notification.receiver.id, notification_data)

        return Response(serializers.RoomTenantSerializer(room_tenant).data)

    @action(detail=True, methods=['post'], url_path='reject-request')
    def reject_request(self, request, pk=None):
        """
        Từ chối yêu cầu thuê phòng
        - Chỉ từ chối yêu cầu đang ở trạng thái PENDING
        - Tạo thông báo cho người thuê
        - Gửi thông báo qua Firebase
        """
        room_tenant = self.get_object()
        if room_tenant.status != RoomTenantStatus.PENDING:
            return Response({"error": "Chỉ có thể từ chối yêu cầu đang ở trạng thái PENDING"},
                            status=status.HTTP_400_BAD_REQUEST)

        room_tenant.status = RoomTenantStatus.CANCELLED
        room_tenant.save()

        Notifications.objects.create(
            receiver=room_tenant.tenant.user,
            title="Yêu cầu bị từ chối",
            content="Yêu cầu thuê phòng của bạn đã bị từ chối",
            notification_type=NotificationType.SYSTEM,
            related_object_id=str(room_tenant.id)
        )

        # Gửi thông báo đến Firebase
        notification = Notifications.objects.latest('created_date')  # Lấy notification vừa tạo
        notification_data = {
            'id': notification.id,
            'title': notification.title,
            'content': notification.content,
            'notification_type': notification.notification_type,
            'created_date': notification.created_date.isoformat(),
            'is_read': notification.is_read
        }
        send_notification(notification.receiver.id, notification_data)

        return Response(serializers.RoomTenantSerializer(room_tenant).data)

    @action(detail=True, methods=['post'], url_path='cancel-contract')
    def cancel_contract(self, request, pk=None):
        """
        Hủy hợp đồng thuê phòng
        - Chỉ hủy hợp đồng đang ở trạng thái ACTIVE
        - Tạo thông báo cho bên còn lại
        - Gửi thông báo qua Firebase
        """
        room_tenant = self.get_object()
        if room_tenant.status != RoomTenantStatus.ACTIVE:
            return Response({"error": "Chỉ có thể hủy hợp đồng đang ở trạng thái ACTIVE"},
                            status=status.HTTP_400_BAD_REQUEST)

        room_tenant.status = RoomTenantStatus.CANCELLED
        room_tenant.save()

        # Thông báo cho bên còn lại dựa vào người thực hiện
        if request.user.role == UserRole.ADMIN:
            receiver = room_tenant.tenant.user
            content = "Hợp đồng của bạn đã bị hủy bởi admin"
        elif request.user == room_tenant.tenant.user:
            receiver = room_tenant.room.motel.user
            content = f"Hợp đồng với {room_tenant.tenant.full_name} đã bị hủy"
        else:  # landlord
            receiver = room_tenant.tenant.user
            content = "Hợp đồng của bạn đã bị hủy bởi chủ trọ"

        Notifications.objects.create(
            receiver=receiver,
            title="Hợp đồng bị hủy",
            content=content,
            notification_type=NotificationType.SYSTEM,
            related_object_id=str(room_tenant.id)
        )

        # Gửi thông báo đến Firebase
        notification = Notifications.objects.latest('created_date')  # Lấy notification vừa tạo
        notification_data = {
            'id': notification.id,
            'title': notification.title,
            'content': notification.content,
            'notification_type': notification.notification_type,
            'created_date': notification.created_date.isoformat(),
            'is_read': notification.is_read
        }
        send_notification(notification.receiver.id, notification_data)

        return Response(serializers.RoomTenantSerializer(room_tenant).data)


class MotelRatingViewSet(viewsets.ViewSet, generics.ListCreateAPIView, generics.RetrieveUpdateDestroyAPIView):
    serializer_class = serializers.MotelRatingSerializer
    pagination_class = paginators.ItemPanigator
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    def get_queryset(self):
        return MotelRating.objects.filter(active=True, motel_id=self.request.query_params.get('motel_id')).select_related('user', 'motel')

    def update_motel_rating(self, motel):
        average_result = motel.motel_ratings.filter(active=True).aggregate(avg=Avg('rating'))
        avg_rating = average_result['avg'] if average_result['avg'] is not None else 0

        motel.rating_score = round(avg_rating, 1)
        motel.save()

    def create_notification(self, rating, action):
        if rating.motel.user != self.request.user:
            Notifications.objects.create(
                receiver=rating.motel.user,
                title="Đánh giá mới",
                content=f"{self.request.user.username} đã {action} nhà trọ {rating.motel.motel_name} của bạn",
                notification_type=NotificationType.SYSTEM,
                related_object_id=rating.id
            )

            # Gửi thông báo đến Firebase
            notification = Notifications.objects.latest('created_date')  # Lấy notification vừa tạo
            notification_data = {
                'id': notification.id,
                'title': notification.title,
                'content': notification.content,
                'notification_type': notification.notification_type,
                'created_date': notification.created_date.isoformat(),
                'is_read': notification.is_read
            }
            send_notification(notification.receiver.id, notification_data)

    def create(self, request, *args, **kwargs):
        try:
            existing_rating = MotelRating.objects.filter(
                motel_id=request.data.get('motel'),
                user=request.user
            ).first()

            if existing_rating:
                serializer = self.get_serializer(existing_rating, data=request.data, partial=True)
                action = "cập nhật"
            else:
                serializer = self.get_serializer(data=request.data)
                action = "đánh giá"

            serializer.is_valid(raise_exception=True)
            rating = serializer.save(user=request.user if not existing_rating else None)

            self.update_motel_rating(rating.motel)
            self.create_notification(rating, action)

            return Response(serializer.data, status=status.HTTP_201_CREATED)

        except Exception as e:
            raise ValidationError(f"Lỗi khi tạo/cập nhật đánh giá: {str(e)}")

    def perform_update(self, serializer):
        rating = serializer.save()
        self.update_motel_rating(rating.motel)
        self.create_notification(rating, "cập nhật")

    def perform_destroy(self, instance):
        motel = instance.motel
        instance.active = False
        instance.save()
        self.update_motel_rating(motel)


class FavoriteViewSet(viewsets.ViewSet, generics.ListAPIView):
    serializer_class = serializers.FavoriteSerializer
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = paginators.ItemPanigator

    def get_queryset(self):
        return self.request.user.favorites.filter(active=True)


class PostViewSet(viewsets.ViewSet, generics.ListCreateAPIView, generics.RetrieveUpdateDestroyAPIView):
    # Lấy tất cả bài viết đang hoạt động
    queryset = Post.objects.filter(active=True)
    # Serializer class để chuyển đổi dữ liệu Post thành JSON và ngược lại
    serializer_class = serializers.PostSerializer
    # Sử dụng phân trang tùy chỉnh cho danh sách bài viết
    pagination_class = paginators.ItemPanigator
    # Yêu cầu người dùng phải đăng nhập và là chủ sở hữu hoặc chỉ có quyền đọc
    permission_classes = [IsAuthenticated, IsOwnerOrReadOnly]

    def get_serializer_class(self):
        if self.action == 'retrieve':
            return serializers.PostDetailSerializer
        return serializers.PostSerializer

    def perform_create(self, serializer):
        # Lưu bài viết mới với người dùng hiện tại là tác giả
        post = serializer.save(user=self.request.user)

        # Xử lý lưu hình ảnh
        images_data = self.request.FILES.getlist('images')
        image_type = self.request.data.get('image_type', 'INSIDE')

        if images_data:
            for order, image in enumerate(images_data):
                PostImage.objects.create(
                    post=post,
                    image_url=image,
                    order=order,
                    image_type=image_type
                )

        if post.post_type == PostType.RENT_OUT and post.motel:
            followers = self.request.user.followers.all()
            for follow in followers:
                Notifications.objects.create(
                    receiver=follow.follower_user,  # Người nhận thông báo là người theo dõi
                    title="New Post",
                    content=f"{self.request.user.username} đã đăng một bài đăng mới: {post.title}",
                    notification_type=NotificationType.NEW_POST,
                    related_object_id=post.id
                )

                # Gửi thông báo đến Firebase
                notification = Notifications.objects.latest('created_date')  # Lấy notification vừa tạo
                notification_data = {
                    'id': notification.id,
                    'title': notification.title,
                    'content': notification.content,
                    'notification_type': notification.notification_type,
                    'created_date': notification.created_date.isoformat(),
                    'is_read': notification.is_read
                }
                send_notification(notification.receiver.id, notification_data)

    def perform_update(self, serializer):
        # Cập nhật bài viết
        post = serializer.save()
        # Xử lý cập nhật hình ảnh nếu có
        if 'images' in self.request.FILES:
            # Xóa các hình ảnh cũ
            post.images.all().delete()
            # Thêm các hình ảnh mới
            for order, image in enumerate(self.request.FILES.getlist('images')):
                PostImage.objects.create(
                    post=post,
                    image_url=image,
                    order=order
                )

    # API endpoint để lấy danh sách bình luận của bài viết
    @action(detail=True, methods=['get'])
    def comments(self, request, pk=None):
        # Lấy bài viết cần xem bình luận
        post = self.get_object()
        comments = Comment.objects.filter(post=post, parent=None)
        serializer = serializers.CommentSerializer(comments, many=True)
        return Response(serializer.data)

    # API endpoint để xóa một hình ảnh cụ thể
    @action(detail=True, methods=['delete'], url_path='images/(?P<image_id>[^/.]+)')
    def delete_image(self, request, pk=None, image_id=None):
        try:
            # Lấy bài viết cần xóa hình ảnh
            post = self.get_object()
            # Lấy hình ảnh cần xóa
            image = post.images.get(id=image_id)
            image.active = False
            image.save()
            return Response(status=status.HTTP_204_NO_CONTENT)
        except PostImage.DoesNotExist:
            return Response(
                {'error': 'Không tìm thấy hình ảnh'},
                status=status.HTTP_204_NO_CONTENT
            )


class CommentViewSet(viewsets.ViewSet, generics.DestroyAPIView, generics.UpdateAPIView):
    # Lấy tất cả bình luận đang hoạt động
    queryset = Comment.objects.filter(active=True)
    # Yêu cầu người dùng phải là chủ sở hữu bình luận hoặc chỉ có quyền đọc
    permission_classes = [IsOwnerOrReadOnly]
    # Serializer class để chuyển đổi dữ liệu Comment thành JSON và ngược lại
    serializer_class = serializers.CommentSerializer
    # Sử dụng phân trang tùy chỉnh cho danh sách bình luận
    pagination_class = paginators.ItemPanigator

    def get_permissions(self):
        if self.action in ['create', 'like_comment', 'reply_comment']:
            return [IsAuthenticated()]
        elif self.action in ['update', 'destroy']:
            return [IsOwnerOrAdmin()]
        return [AllowAny()]

    # lấy danh sách bình luận (Comment) cho một bài viết cụ thể.
    def list(self, request):
        post_id = request.GET.get('post_id')
        if post_id:
            # Chỉ lấy các bình luận gốc (không phải replies), đang hoạt động, thuộc bài viết đó.
            comments = Comment.objects.filter(post=post_id, active=True, parent=None).select_related('user')
        else:
            comments = Comment.objects.filter(active=True, parent=None).select_related('user')
        return Response(serializers.CommentSerializer(comments, many=True, context={"request": request}).data)

    # Tạo mới bình luận gốc
    def create(self, request):
        data = {
            'post': request.data.get('post'),
            'user': request.user.id,
            'content': request.data.get('content')
        }

        if not data['content']:
            return Response({
                'error': 'Nội dung bình luận không được để trống'
            }, status=status.HTTP_400_BAD_REQUEST)

        serializer = serializers.CommentSerializer(data=data, context={'request': request})
        if not serializer.is_valid():
            return Response({
                'error': 'Dữ liệu bình luận không hợp lệ',
                'details': serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)

        comment = serializer.save()

        # Thông báo cho chủ bài viết khi có bình luận mới
        if comment.post.user != request.user:
            Notifications.objects.create(
                receiver=comment.post.user,
                title="Bình luận mới",
                content=f"{request.user.username} đã bình luận bài viết của bạn: {comment.content[:50]}...",
                notification_type=NotificationType.NEW_COMMENT,
                related_object_id=comment.id
            )

            # Gửi thông báo đến Firebase
            notification = Notifications.objects.latest('created_date')  # Lấy notification vừa tạo
            notification_data = {
                'id': notification.id,
                'title': notification.title,
                'content': notification.content,
                'notification_type': notification.notification_type,
                'created_date': notification.created_date.isoformat(),
                'is_read': notification.is_read
            }
            send_notification(notification.receiver.id, notification_data)

        return Response(serializer.data, status=status.HTTP_201_CREATED)

    # Chi tiết 1 bình luận
    def retrieve(self, request, pk=None):
        comment = self.get_object()
        serializer = serializers.CommentSerializer(comment, context={'request': request})
        return Response(serializer.data)

    # Danh sách phản hồi bình luận
    @action(methods=['GET'], detail=True, url_path='replies')
    def get_replies(self, request, pk=None):
        comment = self.get_object()
        replies = Comment.objects.filter(parent=comment, active=True).select_related('user')
        serializer = serializers.CommentSerializer(replies, many=True, context={'request': request})
        return Response(serializer.data)

    # like (thích) cho một bình luận.
    @action(methods=['POST'], detail=True, url_path='like')
    def like_comment(self, request, pk):
        comment = self.get_object()
        like, created = LikeComment.objects.get_or_create(user=request.user, comment=comment)
        if not created:
            like.active = not like.active
        like.save()

        # Thông báo cho người viết bình luận khi có người like
        if like.active and comment.user != request.user:
            Notifications.objects.create(
                receiver=comment.user,
                title="Bình luận được yêu thích",
                content=f"{request.user.username} đã thích bình luận của bạn",
                notification_type=NotificationType.COMMENT_LIKE,
                related_object_id=comment.id
            )

            # Gửi thông báo đến Firebase
            notification = Notifications.objects.latest('created_date')  # Lấy notification vừa tạo
            notification_data = {
                'id': notification.id,
                'title': notification.title,
                'content': notification.content,
                'notification_type': notification.notification_type,
                'created_date': notification.created_date.isoformat(),
                'is_read': notification.is_read
            }
            send_notification(notification.receiver.id, notification_data)

        return Response(serializers.CommentSerializer(comment, context={'request': request}).data)

    # trả lời một bình luận.
    # Lấy danh sách các comment con (replies) của comment hiện tại (parent=comment).
    @action(methods=['POST'], detail=True, url_path='reply')
    def reply_comment(self, request, pk):
        parent = self.get_object()  # Lấy comment cha (parent) và tạo dữ liệu comment mới là reply.
        data = {
            'post': parent.post.id,  # bài viết mà comment cha thuộc về.
            'user': request.user.id,  # người đang gửi request (người trả lời).
            'content': request.data.get('content'),  # nội dung phản hồi, lấy từ request.
            'parent': parent.id  # : gán ID của comment cha để tạo quan hệ cha – con
        }

        serializer = serializers.CommentSerializer(data=data, context={'request': request})
        serializer.is_valid(raise_exception=True)  # nếu dữ liệu không hợp lệ sẽ raise lỗi 400 ngay.
        reply = serializer.save()

        # Thông báo cho người viết bình luận gốc khi có phản hồi
        if parent.user != request.user:
            Notifications.objects.create(
                receiver=parent.user,
                title="Phản hồi bình luận",
                content=f"{request.user.username} đã phản hồi bình luận của bạn: {reply.content[:50]}...",
                notification_type=NotificationType.NEW_COMMENT,
                related_object_id=reply.id
            )

            # Gửi thông báo đến Firebase
            notification = Notifications.objects.latest('created_date')  # Lấy notification vừa tạo
            notification_data = {
                'id': notification.id,
                'title': notification.title,
                'content': notification.content,
                'notification_type': notification.notification_type,
                'created_date': notification.created_date.isoformat(),
                'is_read': notification.is_read
            }
            send_notification(notification.receiver.id, notification_data)

        return Response(serializer.data, status=status.HTTP_201_CREATED)


class SearchHistoryViewSet(viewsets.ModelViewSet):
    # Serializer class để chuyển đổi dữ liệu SearchHistory thành JSON và ngược lại
    serializer_class = serializers.SearchHistorySerializer
    # Yêu cầu người dùng phải đăng nhập để truy cập các API
    permission_classes = [permissions.IsAuthenticated]
    # Sử dụng phân trang tùy chỉnh cho danh sách lịch sử tìm kiếm
    pagination_class = paginators.ItemPanigator

    def get_queryset(self):
        # Kiểm tra nếu là request giả từ Swagger
        if getattr(self, 'swagger_fake_view', False):
            return SearchHistory.objects.none()
        # Trả về danh sách lịch sử tìm kiếm của người dùng hiện tại, sắp xếp theo thời gian tìm kiếm mới nhất
        return SearchHistory.objects.filter(user=self.request.user, active=True).order_by('-search_date')

    def perform_create(self, serializer):
        # Lưu lịch sử tìm kiếm mới với người dùng hiện tại
        serializer.save(user=self.request.user)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        instance.active = False
        instance.save()
        return Response(status=status.HTTP_204_NO_CONTENT)


class FollowViewSet(viewsets.ViewSet, generics.ListAPIView, generics.CreateAPIView):
    # Yêu cầu người dùng phải đăng nhập để truy cập các API
    permission_classes = [permissions.IsAuthenticated]
    # Serializer class để chuyển đổi dữ liệu Follow thành JSON và ngược lại
    serializer_class = serializers.FollowSerializer
    # Sử dụng phân trang tùy chỉnh cho danh sách theo dõi
    pagination_class = paginators.ItemPanigator

    def get_queryset(self):
        if not self.request.user.is_authenticated:
            return Follow.objects.none()
        return Follow.objects.filter(follower_user=self.request.user, active=True).select_related('followed_user').order_by('-created_date')

    def perform_create(self, serializer):
        # Lấy ID người cần theo dõi từ request
        followed_user_id = self.request.data.get('followed_user_id')
        if not followed_user_id:
            raise ValidationError({"error": "Thiếu ID người dùng cần theo dõi"})

        try:
            followed_user = User.objects.get(id=followed_user_id)
        except User.DoesNotExist:
            raise ValidationError({"error": "Người dùng không tồn tại"})

        if followed_user == self.request.user:
            raise ValidationError({"error": "Không thể theo dõi chính mình"})

        # Kiểm tra xem đã follow chưa
        #  Lọc xem người dùng hiện tại (request.user) có đang theo dõi followed_user hay không.
        # Sau khi lọc, .first() sẽ lấy bản ghi đầu tiên nếu có, nếu không có thì trả về None.
        follow = Follow.objects.filter(followed_user=followed_user, follower_user=self.request.user).first()

        if follow:
            follow.active = not follow.active
            follow.save()
            if follow.active:
                # Tạo thông báo khi follow
                Notifications.objects.create(
                    receiver=followed_user,
                    title="Người dùng mới theo dõi",
                    content=f"{self.request.user.username} đã bắt đầu theo dõi bạn",
                    notification_type=NotificationType.FOLLOW,
                    related_object_id=follow.id
                )

                # Gửi thông báo đến Firebase
                notification = Notifications.objects.latest('created_date')  # Lấy notification vừa tạo
                notification_data = {
                    'id': notification.id,
                    'title': notification.title,
                    'content': notification.content,
                    'notification_type': notification.notification_type,
                    'created_date': notification.created_date.isoformat(),
                    'is_read': notification.is_read
                }
                send_notification(notification.receiver.id, notification_data)
            serializer.instance = follow
        else:
            follow = serializer.save(followed_user=followed_user, follower_user=self.request.user, active=True)
            # Tạo thông báo khi follow
            Notifications.objects.create(
                receiver=followed_user,
                title="Người dùng mới theo dõi",
                content=f"{self.request.user.username} đã bắt đầu theo dõi bạn",
                notification_type=NotificationType.FOLLOW,
                related_object_id=follow.id
            )

            # Gửi thông báo đến Firebase
            notification = Notifications.objects.latest('created_date')  # Lấy notification vừa tạo
            notification_data = {
                'id': notification.id,
                'title': notification.title,
                'content': notification.content,
                'notification_type': notification.notification_type,
                'created_date': notification.created_date.isoformat(),
                'is_read': notification.is_read
            }
            send_notification(notification.receiver.id, notification_data)

    def destroy(self, request, pk=None):
        """
        Hủy theo dõi một người dùng
        """
        try:
            # Tìm mối quan hệ theo dõi cần xóa
            follow = Follow.objects.get(follower_user=request.user, followed_user_id=pk, active=True)
            # Xóa mềm mối quan hệ (chỉ cập nhật trạng thái active=False)
            follow.active = False
            follow.save()
            return Response(status=status.HTTP_204_NO_CONTENT)
        except Follow.DoesNotExist:
            return Response({"error": "Không tìm thấy mối quan hệ theo dõi"}, status=status.HTTP_404_NOT_FOUND)

    # API endpoint để lấy danh sách người theo dõi
    @action(detail=False, methods=['get'], url_path='followers')
    def followers(self, request):
        # Lấy danh sách người đang theo dõi người dùng hiện tại
        followers = request.user.followers.filter(active=True).select_related('follower_user').order_by('-created_date')
        # Chuyển đổi dữ liệu thành JSON
        serializer = self.get_serializer(followers, many=True)
        return Response(serializer.data)


class NotificationViewSet(viewsets.ViewSet, generics.ListAPIView, generics.RetrieveAPIView, generics.DestroyAPIView):
    # Lấy tất cả thông báo đang hoạt động
    queryset = Notifications.objects.filter(active=True)
    # Yêu cầu người dùng phải đăng nhập để truy cập các API
    permission_classes = [IsAuthenticated]
    # Serializer class để chuyển đổi dữ liệu Notification thành JSON và ngược lại
    serializer_class = serializers.NotificationSerializer
    # Sử dụng phân trang tùy chỉnh cho danh sách thông báo
    pagination_class = paginators.ItemPanigator

    def get_queryset(self):
        # Kiểm tra nếu là request giả từ Swagger
        if getattr(self, 'swagger_fake_view', False):
            return Notifications.objects.none()
        # Trả về danh sách thông báo của người dùng hiện tại, sắp xếp theo thời gian tạo mới nhất
        return Notifications.objects.filter(receiver=self.request.user, active=True).order_by('-created_date')

    def perform_create(self, serializer):
        # Lưu thông báo mới
        notification = serializer.save()
        # Chuẩn bị dữ liệu thông báo để gửi đến Firebase
        notification_data = {
            'id': notification.id,
            'title': notification.title,
            'content': notification.content,
            'notification_type': notification.notification_type,
            'created_date': notification.created_date.isoformat(),
            'is_read': notification.is_read
        }
        # Gửi thông báo đến Firebase Realtime Database
        send_notification(notification.receiver.id, notification_data)
        return notification

    def perform_destroy(self, instance):
        # Xóa mềm thông báo (chỉ cập nhật trạng thái active=False)
        instance.active = False
        instance.save()

    # API endpoint để lấy danh sách thông báo chưa đọc
    @action(detail=False, methods=['get'], url_path='unread')
    def unread(self, request):
        # Lấy danh sách thông báo chưa đọc của người dùng hiện tại
        notifications = self.get_queryset().filter(is_read=False)
        # Chuyển đổi dữ liệu thành JSON
        serializer = self.serializer_class(notifications, many=True)
        return Response(serializer.data)

    # API endpoint để đánh dấu một thông báo là đã đọc
    @action(detail=True, methods=['put'], url_path='read')
    def read(self, request, pk=None):
        try:
            # Lấy thông báo cần đánh dấu đã đọc
            notification = self.get_object()
            # Cập nhật trạng thái đã đọc
            notification.is_read = True
            notification.save()
            return Response({'message': 'Thông báo được đánh dấu là đã đọc'})
        except Notifications.DoesNotExist:
            return Response({'error': 'Không tìm thấy thông báo'}, status=status.HTTP_200_OK)

    # API endpoint để đánh dấu tất cả thông báo là đã đọc
    @action(detail=False, methods=['put'], url_path='read_all')
    def read_all(self, request):
        # Cập nhật trạng thái đã đọc cho tất cả thông báo chưa đọc
        self.get_queryset().filter(is_read=False).update(is_read=True)
        return Response({'message': 'Tất cả thông báo được đánh dấu là đã đọc'})

    # API endpoint để xóa tất cả thông báo
    @action(detail=False, methods=['delete'], url_path='delete_all')
    def delete_all(self, request):
        # Xóa mềm tất cả thông báo (cập nhật trạng thái active=False)
        self.get_queryset().update(active=False)
        return Response({'message': 'Tất cả thông báo đã bị xóa'})

    # API endpoint để đếm số thông báo chưa đọc
    @action(detail=False, methods=['get'], url_path='unread_count')
    def unread_count(self, request):
        # Đếm số lượng thông báo chưa đọc
        count = self.get_queryset().filter(is_read=False).count()
        return Response({'unread_count': count})

    # API endpoint để lọc thông báo theo loại
    @action(detail=False, methods=['get'], url_path='by_type')
    def by_type(self, request):
        # Lấy loại thông báo từ query parameters
        notification_type = request.query_params.get('type')
        # Kiểm tra xem có loại thông báo được chỉ định không
        if not notification_type:
            return Response({'error': 'Notification type là bắt buộc'}, status=status.HTTP_400_BAD_REQUEST)

        # Lọc thông báo theo loại
        notifications = self.get_queryset().filter(notification_type=notification_type)
        # Chuyển đổi dữ liệu thành JSON
        serializer = self.serializer_class(notifications, many=True)
        return Response(serializer.data)


class ChatRoomViewSet(viewsets.ModelViewSet):
    # Serializer class để chuyển đổi dữ liệu ChatRoom thành JSON và ngược lại
    serializer_class = serializers.ChatRoomSerializer
    # Yêu cầu người dùng phải đăng nhập để truy cập các API
    permission_classes = [permissions.IsAuthenticated]
    # Sử dụng phân trang tùy chỉnh cho danh sách phòng chat
    pagination_class = paginators.ItemPanigator

    def get_queryset(self):
        # Kiểm tra nếu là request giả từ Swagger
        if getattr(self, 'swagger_fake_view', False):
            return ChatRoom.objects.none()
        # Trả về danh sách phòng chat của người dùng hiện tại, sắp xếp theo thời gian cập nhật mới nhất
        return self.request.user.chat_rooms.filter(active=True).order_by('-updated_date')

    def perform_create(self, serializer):
        # Lưu phòng chat mới
        chat_room = serializer.save()
        # Thêm người dùng hiện tại vào danh sách thành viên của phòng chat
        chat_room.participants.add(self.request.user)
        # Lấy danh sách ID người tham gia từ request data
        participants = self.request.data.get('participants', [])
        # Thêm từng người tham gia vào phòng chat
        for participant_id in participants:
            try:
                # Tìm user theo ID
                user = User.objects.get(id=participant_id)
                # Thêm user vào phòng chat
                chat_room.participants.add(user)
            except User.DoesNotExist:
                # Bỏ qua nếu không tìm thấy user
                continue


class MessageViewSet(viewsets.ViewSet, generics.ListCreateAPIView, generics.RetrieveUpdateDestroyAPIView):
    # Serializer class để chuyển đổi dữ liệu Message thành JSON và ngược lại
    serializer_class = serializers.MessageSerializer
    # Yêu cầu người dùng phải đăng nhập để truy cập các API
    permission_classes = [permissions.IsAuthenticated]
    # Sử dụng phân trang tùy chỉnh cho danh sách tin nhắn
    pagination_class = paginators.ItemPanigator

    def get_queryset(self):
        # Lấy ID phòng chat từ URL parameters
        chat_room_id = self.kwargs.get('chat_room_id')
        # Trả về danh sách tin nhắn của phòng chat, sắp xếp theo thời gian tạo
        return Message.objects.filter(chat_room_id=chat_room_id, active=True).order_by('created_date')

    def perform_create(self, serializer):
        # Lấy ID phòng chat từ URL parameters
        chat_room_id = self.kwargs.get('chat_room_id')
        try:
            # Tìm phòng chat theo ID
            chat_room = ChatRoom.objects.get(id=chat_room_id)
            # Kiểm tra xem người dùng hiện tại có phải là thành viên của phòng chat không
            if self.request.user not in chat_room.participants.all():
                raise PermissionDenied("Bạn không có quyền gửi tin nhắn trong phòng chat này")
            # Lưu tin nhắn mới với người gửi là user hiện tại
            message = serializer.save(sender=self.request.user, chat_room=chat_room)

            # Lấy channel layer để gửi thông báo qua WebSocket
            channel_layer = get_channel_layer()
            # Gửi tin nhắn mới đến tất cả thành viên trong phòng chat qua WebSocket
            async_to_sync(channel_layer.group_send)(
                f'chat_{chat_room_id}',
                {
                    'type': 'chat_message',
                    'message': {
                        'id': message.id,
                        'content': message.content,
                        'sender_id': message.sender.id,
                        'sender_name': message.sender.username,
                        'created_date': message.created_date.isoformat(),
                        'is_read': message.is_read
                    }
                }
            )
        except ChatRoom.DoesNotExist:
            raise NotFound("Không tìm thấy phòng chat")

    def perform_update(self, serializer):
        # Lấy tin nhắn cần cập nhật
        message = serializer.instance
        # Kiểm tra xem người dùng hiện tại có phải là người gửi tin nhắn không
        if message.sender != self.request.user:
            raise PermissionDenied("Bạn không có quyền chỉnh sửa tin nhắn này")
        # Lưu tin nhắn đã cập nhật
        message = serializer.save()

        # Lấy channel layer để gửi thông báo qua WebSocket
        channel_layer = get_channel_layer()
        # Gửi thông báo cập nhật tin nhắn đến tất cả thành viên trong phòng chat
        async_to_sync(channel_layer.group_send)(
            f'chat_{message.chat_room.id}',
            {
                'type': 'message_update',
                'message': {
                    'id': message.id,
                    'content': message.content,
                    'sender_id': message.sender.id,
                    'sender_name': message.sender.username,
                    'created_date': message.created_date.isoformat(),
                    'is_read': message.is_read,
                    'action': 'update'
                }
            }
        )

    def perform_destroy(self, instance):
        # Kiểm tra xem người dùng hiện tại có phải là người gửi tin nhắn không
        if instance.sender != self.request.user:
            raise PermissionDenied("Bạn không có quyền xóa tin nhắn này")
        # Lưu ID phòng chat để gửi thông báo sau khi xóa
        chat_room_id = instance.chat_room.id
        # Xóa mềm tin nhắn (chỉ cập nhật trạng thái active=False)
        instance.active = False
        instance.save()

        # Lấy channel layer để gửi thông báo qua WebSocket
        channel_layer = get_channel_layer()
        # Gửi thông báo xóa tin nhắn đến tất cả thành viên trong phòng chat
        async_to_sync(channel_layer.group_send)(
            f'chat_{chat_room_id}',
            {
                'type': 'message_update',
                'message': {
                    'id': instance.id,
                    'action': 'delete'
                }
            }
        )

    @action(detail=True, methods=['put'], url_path='read')
    def read(self, request, chat_room_id=None, pk=None):
        # Lấy tin nhắn cần đánh dấu đã đọc
        message = self.get_object()
        # Cập nhật trạng thái đã đọc
        message.is_read = True
        message.save()

        # Lấy channel layer để gửi thông báo qua WebSocket
        channel_layer = get_channel_layer()
        # Gửi thông báo trạng thái đã đọc đến tất cả thành viên trong phòng chat
        async_to_sync(channel_layer.group_send)(
            f'chat_{chat_room_id}',
            {
                'type': 'message_update',
                'message': {
                    'id': message.id,
                    'is_read': True,
                    'action': 'read'
                }
            }
        )
        return Response({'status': 'tin nhắn được đánh dấu là đã đọc'})


class PaymentViewSet(viewsets.ViewSet, generics.ListCreateAPIView, generics.RetrieveUpdateDestroyAPIView):
    """
    ViewSet quản lý thanh toán
    - Cho phép xem danh sách, chi tiết, tạo mới, cập nhật và xóa thanh toán
    - Có phân quyền truy cập dựa trên vai trò người dùng
    - Tự động gửi thông báo khi có thanh toán mới hoặc cập nhật
    """
    # Serializer chuyển đổi dữ liệu thanh toán
    serializer_class = serializers.PaymentSerializer
    # Yêu cầu đăng nhập để truy cập các API
    permission_classes = [permissions.IsAuthenticated]
    # Phân trang tùy chỉnh
    pagination_class = paginators.ItemPanigator

    def get_permissions(self):
        """
        Xác định quyền truy cập cho từng action
        - list, create, update_status: Yêu cầu đăng nhập
        - retrieve, update, destroy: Yêu cầu đăng nhập và là chủ sở hữu hoặc chủ nhà
        """
        if self.action in ['list', 'create', 'update_status']:
            return [permissions.IsAuthenticated()]
        elif self.action in ['retrieve', 'update', 'partial_update', 'destroy']:
            return [permissions.IsAuthenticated(), IsPaymentOwnerOrMotelOwner()]
        return [permissions.IsAuthenticated()]

    def get_queryset(self):
        """
        Lấy danh sách thanh toán dựa trên vai trò người dùng
        - Admin: xem tất cả thanh toán
        - Chủ trọ: xem thanh toán của các phòng trong nhà trọ của mình
        - Người thuê: chỉ xem thanh toán của mình
        """
        # Kiểm tra nếu là request giả từ Swagger
        if getattr(self, 'swagger_fake_view', False):
            return Payment.objects.none()

        # Kiểm tra xem user có được xác thực không
        if not self.request.user.is_authenticated:
            return Payment.objects.none()

        # Lấy tất cả thanh toán đang hoạt động và join các bảng liên quan
        queryset = Payment.objects.filter(active=True).select_related(
            'payer',  # Người thanh toán
            'room',   # Phòng được thanh toán
            'room__motel',  # Nhà trọ chứa phòng
            'room__motel__user'  # Chủ nhà trọ
        )
        user = self.request.user

        # Admin có thể xem tất cả thanh toán
        if user.is_staff:
            return queryset

        # Chủ trọ chỉ xem được thanh toán của các phòng trong nhà trọ của mình
        if user.role == UserRole.LANDLORD:
            return queryset.filter(room__motel__user=user)

        # Người thuê chỉ xem được thanh toán của mình
        return queryset.filter(payer=user)

    def perform_create(self, serializer):
        """
        Tạo thanh toán mới
        - Lưu thanh toán với người thanh toán là user hiện tại
        - Tạo thông báo cho chủ nhà
        - Gửi thông báo qua Firebase
        """
        # Lưu thanh toán mới
        payment = serializer.save(payer=self.request.user)

        # Tạo thông báo cho chủ nhà
        Notifications.objects.create(
            receiver=payment.room.motel.user,
            title="Thanh toán mới",
            content=f"Có thanh toán mới cho phòng {payment.room.room_name} từ {self.request.user.username}",
            notification_type=NotificationType.PAYMENT,
            related_object_id=payment.id
        )

        # Gửi thông báo đến Firebase
        notification = Notifications.objects.latest('created_date')
        notification_data = {
            'id': notification.id,
            'title': notification.title,
            'content': notification.content,
            'notification_type': notification.notification_type,
            'created_date': notification.created_date.isoformat(),
            'is_read': notification.is_read
        }
        send_notification(notification.receiver.id, notification_data)

    def perform_update(self, serializer):
        """
        Cập nhật thông tin thanh toán
        - Lưu thông tin cập nhật
        - Tạo thông báo cho người thanh toán
        - Gửi thông báo qua Firebase
        """
        # Lưu thông tin cập nhật
        payment = serializer.save()

        # Tạo thông báo cho người thanh toán
        Notifications.objects.create(
            receiver=payment.payer,
            title="Cập nhật thanh toán",
            content=f"Thanh toán của bạn cho phòng {payment.room.room_name} đã được cập nhật",
            notification_type=NotificationType.PAYMENT,
            related_object_id=payment.id
        )

        # Gửi thông báo đến Firebase
        notification = Notifications.objects.latest('created_date')
        notification_data = {
            'id': notification.id,
            'title': notification.title,
            'content': notification.content,
            'notification_type': notification.notification_type,
            'created_date': notification.created_date.isoformat(),
            'is_read': notification.is_read
        }
        send_notification(notification.receiver.id, notification_data)

    @action(detail=True, methods=['patch'], url_path='update-status')
    def update_status(self, request, pk=None):
        """
        Cập nhật trạng thái thanh toán
        - Kiểm tra trạng thái mới có hợp lệ không
        - Cập nhật trạng thái
        - Tạo thông báo cho người thanh toán và chủ nhà
        - Gửi thông báo qua Firebase
        """
        # Lấy thanh toán cần cập nhật
        payment = self.get_object()
        # Lấy trạng thái mới từ request
        new_status = request.data.get('status')

        # Lấy danh sách trạng thái hợp lệ
        valid_statuses = []
        for choice in PaymentStatus.choices:
            status_code = choice[0]  # phần tử đầu tiên trong tuple (code, label)
            valid_statuses.append(status_code)

        # Kiểm tra trạng thái mới có hợp lệ không
        if new_status not in valid_statuses:
            raise ValidationError({
                "error": "Trạng thái không hợp lệ",
                "detail": f"Trạng thái phải là một trong các giá trị: {valid_statuses}"
            })

        # Cập nhật trạng thái
        payment.status = new_status
        payment.save()

        # Thông báo cho người thanh toán khi trạng thái thay đổi
        Notifications.objects.create(
            receiver=payment.payer,
            title="Cập nhật trạng thái thanh toán",
            content=f"Thanh toán của bạn cho phòng {payment.room.room_name} đã được cập nhật trạng thái: {payment.status}",
            notification_type=NotificationType.PAYMENT,
            related_object_id=payment.id
        )

        # Gửi thông báo đến Firebase
        notification = Notifications.objects.latest('created_date')
        notification_data = {
            'id': notification.id,
            'title': notification.title,
            'content': notification.content,
            'notification_type': notification.notification_type,
            'created_date': notification.created_date.isoformat(),
            'is_read': notification.is_read
        }
        send_notification(notification.receiver.id, notification_data)

        # Nếu trạng thái là COMPLETED hoặc FAILED, tạo thông báo cho chủ nhà
        if new_status in [PaymentStatus.COMPLETED, PaymentStatus.FAILED]:
            status_text = "thành công" if new_status == PaymentStatus.COMPLETED else "thất bại"
            Notifications.objects.create(
                receiver=payment.room.motel.user,
                title=f"Thanh toán {status_text}",
                content=f"Thanh toán cho phòng {payment.room.room_name} từ {payment.payer.username} đã {status_text}",
                notification_type=NotificationType.PAYMENT,
                related_object_id=payment.id
            )

            # Gửi thông báo đến Firebase
            notification = Notifications.objects.latest('created_date')
            notification_data = {
                'id': notification.id,
                'title': notification.title,
                'content': notification.content,
                'notification_type': notification.notification_type,
                'created_date': notification.created_date.isoformat(),
                'is_read': notification.is_read
            }
            send_notification(notification.receiver.id, notification_data)

        # Trả về thông tin thanh toán đã cập nhật
        serializer = self.get_serializer(payment)
        return Response(serializer.data)

    def perform_destroy(self, instance):
        """
        Xóa mềm thanh toán (chỉ cập nhật trạng thái active=False)
        - Chỉ cho phép admin hoặc chủ nhà xóa
        """
        user = self.request.user
        # Kiểm tra quyền xóa
        if not (user.is_staff or instance.room.motel in user.motels.all()):
            raise PermissionDenied("Chỉ admin hoặc chủ nhà mới được phép xóa thanh toán")
        # Xóa mềm
        instance.active = False
        instance.save()

    @action(detail=False, methods=['get'], url_path='room/(?P<room_id>[^/.]+)')
    def room_payments(self, request, room_id=None):
        """
        Lấy danh sách thanh toán của một phòng
        - Chỉ cho phép admin hoặc chủ nhà xem
        - Trả về danh sách thanh toán của phòng được chỉ định
        """
        try:
            # Lấy thông tin phòng
            room = Room.objects.get(id=room_id)
            # Kiểm tra quyền xem
            if not (request.user.is_staff or request.user == room.motel.user):
                return Response(
                    {'error': 'Không có quyền xem thanh toán của phòng này'},
                    status=status.HTTP_403_FORBIDDEN
                )
            # Lấy danh sách thanh toán của phòng
            payments = self.get_queryset().filter(room=room)
            serializer = self.get_serializer(payments, many=True)
            return Response(serializer.data)
        except Room.DoesNotExist:
            return Response(
                {'error': 'Phòng không tồn tại'},
                status=status.HTTP_404_NOT_FOUND
            )

    @action(detail=False, methods=['get'], url_path='status/(?P<status>[^/.]+)')
    def status_payments(self, request, status=None):
        """
        Lấy danh sách thanh toán theo trạng thái
        - Kiểm tra trạng thái có hợp lệ không
        - Trả về danh sách thanh toán có trạng thái được chỉ định
        """
        # Lấy danh sách trạng thái hợp lệ
        valid_statuses = []
        for choice in PaymentStatus.choices:
            status_code = choice[0]  # phần tử đầu tiên trong tuple (code, label)
            valid_statuses.append(status_code)

        # Kiểm tra trạng thái có hợp lệ không
        if status not in valid_statuses:
            return Response(
                {'error': 'Trạng thái không hợp lệ'},
                status=status.HTTP_404_NOT_FOUND
            )

        # Lấy danh sách thanh toán theo trạng thái
        payments = self.get_queryset().filter(status=status)
        serializer = self.get_serializer(payments, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'], url_path='method/(?P<method>[^/.]+)')
    def method_payments(self, request, method=None):
        """
        Lấy danh sách thanh toán theo phương thức thanh toán
        - Kiểm tra phương thức thanh toán có hợp lệ không
        - Trả về danh sách thanh toán sử dụng phương thức được chỉ định
        """
        # Lấy danh sách phương thức thanh toán hợp lệ
        valid_methods = []
        for choice in PaymentMethod.choices:
            method_code = choice[0]
            valid_methods.append(method_code)

        # Kiểm tra phương thức thanh toán có hợp lệ không
        if method not in valid_methods:
            return Response(
                {'error': 'Phương thức thanh toán không hợp lệ'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Lấy danh sách thanh toán theo phương thức
        payments = self.get_queryset().filter(payment_method=method)
        serializer = self.get_serializer(payments, many=True)
        return Response(serializer.data)


class SearchViewSet(viewsets.ViewSet):
    """
    ViewSet xử lý tìm kiếm nhà trọ
    - Cung cấp API tìm kiếm theo nhiều tiêu chí
    - Hỗ trợ tìm kiếm theo vị trí địa lý
    - Lưu lịch sử tìm kiếm cho người dùng đã đăng nhập
    """

    def list(self, request):
        """
        API endpoint tìm kiếm nhà trọ theo nhiều tiêu chí
        - Tìm kiếm theo từ khóa
        - Lọc theo địa điểm (quận/huyện, thành phố, tỉnh)
        - Lọc theo khoảng giá
        - Lọc theo số người tối đa
        - Lọc theo tiện nghi
        """
        # Lấy từ khóa tìm kiếm từ query params
        search_query = request.query_params.get('q')
        if search_query:
            # Tìm kiếm theo tên nhà trọ hoặc mô tả
            motels = Motel.objects.filter(
                Q(motel_name__icontains=search_query) |
                Q(description__icontains=search_query)
            )
        else:
            # Nếu không có từ khóa, lấy tất cả nhà trọ
            motels = Motel.objects.all()

            # Lọc theo quận/huyện nếu có
            district = request.query_params.get('district')
            if district:
                motels = motels.filter(district__icontains=district)

            # Lọc theo thành phố nếu có
            city = request.query_params.get('city')
            if city:
                motels = motels.filter(city__icontains=city)

            # Lọc theo tỉnh nếu có
            province = request.query_params.get('province')
            if province:
                motels = motels.filter(province__icontains=province)

            # Lọc theo khoảng giá
            min_price = request.query_params.get('min_price')
            max_price = request.query_params.get('max_price')
            if min_price or max_price:
                try:
                    # Chuyển đổi giá trị sang float
                    min_price = float(min_price) if min_price else None
                    max_price = float(max_price) if max_price else None

                    # Tìm kiếm trong bảng Post (bài đăng cho thuê)
                    post_query = Post.objects.filter(motel=OuterRef('pk'))
                    if min_price:
                        post_query = post_query.filter(min_price__gte=min_price)
                    if max_price:
                        post_query = post_query.filter(max_price__lte=max_price)

                    # Tìm kiếm trong bảng Room (phòng trọ)
                    room_query = Room.objects.filter(motel=OuterRef('pk'))
                    if min_price:
                        room_query = room_query.filter(price__gte=min_price)
                    if max_price:
                        room_query = room_query.filter(price__lte=max_price)

                    # Kết hợp kết quả từ cả hai bảng
                    motels = motels.filter(
                        Q(id__in=Subquery(post_query.values('motel_id'))) |
                        Q(id__in=Subquery(room_query.values('motel_id')))
                    )
                except ValueError:
                    # Bỏ qua điều kiện tìm kiếm theo giá nếu giá trị không hợp lệ
                    pass

            # Lọc theo số người tối đa
            max_people = request.query_params.get('max_people')
            if max_people:
                # Tìm các phòng có số người tối đa phù hợp
                room_query = Room.objects.filter(motel=OuterRef('pk'), max_people__lte=max_people)
                motels = motels.filter(id__in=Subquery(room_query.values('motel_id')))

            # Tìm kiếm theo tiện nghi
            amenities = request.query_params.getlist('amenities')
            if amenities:
                # Tìm các phòng có chứa ít nhất một trong các tiện nghi được chọn
                room_query = Room.objects.filter(
                    motel=OuterRef('pk'),
                    amenities__id__in=amenities
                )
                motels = motels.filter(id__in=Subquery(room_query.values('motel_id')))

        # Lưu lịch sử tìm kiếm nếu người dùng đã đăng nhập
        if request.user.is_authenticated:
            # Tạo dictionary chứa các tham số tìm kiếm
            search_params = {
                'q': search_query,
                'district': request.query_params.get('district'),
                'city': request.query_params.get('city'),
                'province': request.query_params.get('province'),
                'min_price': request.query_params.get('min_price'),
                'max_price': request.query_params.get('max_price'),
                'max_people': request.query_params.get('max_people'),
                'amenities': request.query_params.getlist('amenities')
            }
            # Chỉ lưu các tham số không None và không rỗng
            search_params = {k: v for k, v in search_params.items() if v is not None and v != []}

            # Tạo bản ghi lịch sử tìm kiếm nếu có ít nhất một tham số
            if search_params:
                SearchHistory.objects.create(
                    user=request.user,
                    search_params=search_params
                )

        # Chuyển đổi kết quả thành JSON và trả về
        serializer = serializers.MotelSerializer(motels.distinct(), many=True, context={'request': request})
        return Response(serializer.data)

    @action(detail=False, methods=['get'], url_path='nearby')
    def nearby(self, request):
        """
        API tìm kiếm nhà trọ xung quanh một vị trí
        Query Parameters:
        - latitude: Vĩ độ (float)
        - longitude: Kinh độ (float)
        - radius: Bán kính tìm kiếm tính bằng km (float)
        """
        try:
            # Lấy các tham số từ request
            latitude = float(request.query_params.get('latitude'))  # Vĩ độ
            longitude = float(request.query_params.get('longitude'))  # Kinh độ
            radius = float(request.query_params.get('radius', 5))  # Bán kính tìm kiếm (mặc định 5km)

            # Kiểm tra giá trị tọa độ hợp lệ
            if not (-90 <= latitude <= 90) or not (-180 <= longitude <= 180):
                return Response(
                    {"error": "Tọa độ không hợp lệ"},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Lấy tất cả nhà trọ có tọa độ
            motels = Motel.objects.filter(
                active=True,
                latitude__isnull=False,
                longitude__isnull=False
            )

            # Lọc nhà trọ trong bán kính
            nearby_motels = []
            for motel in motels:
                # Tính khoảng cách từ vị trí hiện tại đến nhà trọ
                distance = calculate_distance(
                    latitude,
                    longitude,
                    motel.latitude,
                    motel.longitude
                )
                # Thêm vào danh sách nếu trong bán kính
                if distance <= radius:
                    motel.distance = distance  # Thêm khoảng cách vào object
                    nearby_motels.append(motel)

            # Sắp xếp theo khoảng cách (gần nhất lên đầu)
            nearby_motels.sort(key=lambda x: x.distance)

            # Phân trang kết quả
            paginator = paginators.ItemPanigator()
            result_page = paginator.paginate_queryset(nearby_motels, request)

            # Chuyển đổi kết quả thành JSON
            serializer = serializers.MotelSerializer(result_page, many=True, context={'request': request})

            # Thêm khoảng cách vào kết quả
            response_data = serializer.data
            for i, motel in enumerate(result_page):
                response_data[i]['distance'] = round(motel.distance, 2)

            # Ghi log thông tin tìm kiếm
            logger.info(f"Tìm kiếm nhà trọ gần vị trí: {latitude}, {longitude}")

            # Trả về kết quả đã phân trang
            return paginator.get_paginated_response(response_data)

        except (ValueError, TypeError):
            # Xử lý lỗi khi tham số không hợp lệ
            return Response(
                {"error": "Tham số không hợp lệ"},
                status=400
            )
        except Exception as e:
            # Xử lý các lỗi khác
            logger.error(f"Lỗi khi tìm kiếm nhà trọ: {str(e)}")
            return Response(
                {"error": "Có lỗi xảy ra khi tìm kiếm"},
                status=500
            )


class StatisticsViewSet(viewsets.ViewSet):
    """
    ViewSet quản lý thống kê dữ liệu
    - Chỉ cho phép admin truy cập
    - Cung cấp các API thống kê số lượng người dùng và chủ trọ
    """
    # Chỉ cho phép admin truy cập các API trong ViewSet này
    permission_classes = [permissions.IsAdminUser]

    def _parse_date(self, date_str):
        """
        Chuyển đổi chuỗi ngày thành đối tượng datetime có timezone.
        - Xử lý chuỗi ngày theo định dạng YYYY-MM-DD
        - Thêm timezone UTC cho datetime
        - Trả về None nếu chuỗi không hợp lệ
        """
        # Kiểm tra nếu không có chuỗi ngày thì trả về None
        if not date_str:
            return None
        try:
            # Phân tích chuỗi ngày và làm cho nó nhận biết múi giờ
            naive_dt = datetime.strptime(date_str, '%Y-%m-%d')
            # Thêm timezone UTC cho datetime
            return timezone.make_aware(naive_dt, timezone=pytz.UTC)
        except ValueError:
            # Trả về None nếu chuỗi ngày không hợp lệ
            return None

    @action(detail=False, methods=['get'], url_path='landlords')
    def landlord_count(self, request):
        """
        Thống kê số lượng chủ trọ theo ngày, tháng, năm, quý.
        - Lọc theo khoảng thời gian (from_date, to_date)
        - Nhóm theo đơn vị thời gian (day, month, year, quarter)
        - Trả về số lượng chủ trọ cho mỗi khoảng thời gian
        """
        # Lấy và xử lý các tham số từ request
        from_date = self._parse_date(request.query_params.get('from'))  # Lấy ngày bắt đầu từ query params
        to_date = self._parse_date(request.query_params.get('to'))      # Lấy ngày kết thúc từ query params
        type_ = request.query_params.get('type', 'month')              # Lấy loại thống kê (mặc định là theo tháng)

        # Lấy tất cả chủ trọ
        queryset = Landlord.objects.all()

        # Lọc theo khoảng thời gian nếu có
        if from_date:
            queryset = queryset.filter(created_date__gte=from_date)  # Lọc từ ngày bắt đầu
        if to_date:
            queryset = queryset.filter(created_date__lte=to_date)    # Lọc đến ngày kết thúc

        # Thống kê theo ngày
        if type_ == 'day':
            # Sử dụng extra để thêm trường day từ created_date và đếm số lượng
            data = queryset.extra({'day': "DATE(created_date)"}).values('day').annotate(count=Count('user_id')).order_by('day')

        # Thống kê theo tháng
        elif type_ == 'month':
            # Sử dụng DATE_FORMAT để lấy năm-tháng và đếm số lượng
            data = queryset.extra({'month': "DATE_FORMAT(created_date, '%%Y-%%m')"}).values('month').annotate(count=Count('user_id')).order_by('month')

        # Thống kê theo năm
        elif type_ == 'year':
            # Sử dụng DATE_FORMAT để lấy năm và đếm số lượng
            data = queryset.extra({'year': "DATE_FORMAT(created_date, '%%Y')"}).values('year').annotate(count=Count('user_id')).order_by('year')

        # Thống kê theo quý
        elif type_ == 'quarter':
            # Sử dụng QUARTER để lấy quý và đếm số lượng
            data = queryset.extra({
                'year': "DATE_FORMAT(created_date, '%%Y')",
                'quarter': "QUARTER(created_date)"
            }).values('year', 'quarter').annotate(count=Count('user_id')).order_by('year', 'quarter')
        else:
            # Trả về lỗi nếu type không hợp lệ
            return Response({'error': 'type phải là day, month, year, quarter'})

        # Trả về kết quả thống kê
        return Response(data)

    @action(detail=False, methods=['get'], url_path='users')
    def user_count(self, request):
        """
        Thống kê số lượng người dùng theo ngày, tháng, năm, quý.
        - Lọc theo khoảng thời gian (from_date, to_date)
        - Nhóm theo đơn vị thời gian (day, month, year, quarter)
        - Trả về số lượng người dùng cho mỗi khoảng thời gian
        """
        # Lấy và xử lý các tham số từ request
        from_date = self._parse_date(request.query_params.get('from'))  # Lấy ngày bắt đầu từ query params
        to_date = self._parse_date(request.query_params.get('to'))      # Lấy ngày kết thúc từ query params
        type_ = request.query_params.get('type', 'month')              # Lấy loại thống kê (mặc định là theo tháng)

        # Lấy tất cả người dùng đang hoạt động
        queryset = User.objects.filter(is_active=True)

        # Lọc theo khoảng thời gian nếu có
        if from_date:
            queryset = queryset.filter(created_date__gte=from_date)  # Lọc từ ngày bắt đầu
        if to_date:
            queryset = queryset.filter(created_date__lte=to_date)    # Lọc đến ngày kết thúc

        # Thống kê theo ngày
        if type_ == 'day':
            # Sử dụng extra để thêm trường day từ created_date và đếm số lượng
            data = queryset.extra({'day': "DATE(created_date)"}).values('day').annotate(count=Count('id')).order_by('day')

        # Thống kê theo tháng
        elif type_ == 'month':
            # Sử dụng DATE_FORMAT để lấy năm-tháng và đếm số lượng
            data = queryset.extra({'month': "DATE_FORMAT(created_date, '%%Y-%%m')"}).values('month').annotate(count=Count('id')).order_by('month')

        # Thống kê theo năm
        elif type_ == 'year':
            # Sử dụng DATE_FORMAT để lấy năm và đếm số lượng
            data = queryset.extra({'year': "DATE_FORMAT(created_date, '%%Y')"}).values('year').annotate(count=Count('id')).order_by('year')

        # Thống kê theo quý
        elif type_ == 'quarter':
            # Sử dụng QUARTER để lấy quý và đếm số lượng
            data = queryset.extra({
                'year': "DATE_FORMAT(created_date, '%%Y')",
                'quarter': "QUARTER(created_date)"
            }).values('year', 'quarter').annotate(count=Count('id')).order_by('year', 'quarter')
        else:
            # Trả về lỗi nếu type không hợp lệ
            return Response({'error': 'type phải là day, month, year, quarter'})

        # Trả về kết quả thống kê
        return Response(data)


class VNPayViewSet(viewsets.ViewSet):
    """
    ViewSet xử lý các thao tác liên quan đến thanh toán VNPay
    - Tạo URL thanh toán
    - Xử lý kết quả trả về từ VNPay
    """

    def get_client_ip(self, request):
        """
        Lấy địa chỉ IP của client gửi request
        - Kiểm tra header X-Forwarded-For trước
        - Nếu không có thì lấy từ REMOTE_ADDR
        """
        # Lấy IP từ header X-Forwarded-For (thường được set bởi proxy/load balancer)
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            # Lấy IP đầu tiên trong danh sách (IP thật của client)
            ip = x_forwarded_for.split(',')[0]
        else:
            # Nếu không có X-Forwarded-For, lấy IP trực tiếp từ request
            ip = request.META.get('REMOTE_ADDR')
        return ip

    @action(detail=False, methods=['post'], url_path='create')
    def create_payment(self, request):
        """
        Tạo URL thanh toán VNPay và trả về cho client
        Quy trình:
        1. Nhận thông tin thanh toán từ client (order_id, amount, etc.)
        2. Khởi tạo đối tượng VNPay và set các thông tin cần thiết
        3. Tạo URL thanh toán với chữ ký bảo mật
        4. Trả về URL cho client để chuyển hướng đến trang thanh toán VNPay
        """
        try:
            # Lấy dữ liệu từ request
            data = request.data
            order_id = data.get('order_id')  # ID đơn hàng
            amount = data.get('amount')  # Số tiền thanh toán
            order_desc = data.get('order_desc', 'Thanh toan phong tro')  # Mô tả đơn hàng
            order_type = data.get('order_type', 'other')  # Loại đơn hàng
            bank_code = data.get('bank_code', '')  # Mã ngân hàng (nếu có)
            language = data.get('language', 'vn')  # Ngôn ngữ hiển thị

            # Kiểm tra dữ liệu đầu vào
            if not order_id or not amount:
                return Response({
                    'error': 'Thiếu thông tin đơn hàng hoặc số tiền'
                }, status=status.HTTP_400_BAD_REQUEST)

            if amount <= 0:
                return Response({
                    'error': 'Số tiền thanh toán phải lớn hơn 0'
                }, status=status.HTTP_400_BAD_REQUEST)

            # Lấy IP của client
            ipaddr = self.get_client_ip(request)

            # Khởi tạo đối tượng VNPay và set các thông tin
            vnp = vnpay()
            vnp.requestData['vnp_Version'] = '2.1.0'  # Phiên bản API VNPay
            vnp.requestData['vnp_Command'] = 'pay'    # Lệnh thanh toán
            vnp.requestData['vnp_TmnCode'] = settings.VNPAY_TMN_CODE  # Mã website tại VNPAY
            vnp.requestData['vnp_Amount'] = amount * 100  # Số tiền * 100 (VNPay yêu cầu)
            vnp.requestData['vnp_CurrCode'] = 'VND'   # Đơn vị tiền tệ
            vnp.requestData['vnp_TxnRef'] = order_id  # Mã đơn hàng
            vnp.requestData['vnp_OrderInfo'] = order_desc  # Mô tả đơn hàng
            vnp.requestData['vnp_OrderType'] = order_type  # Loại đơn hàng
            vnp.requestData['vnp_Locale'] = language  # Ngôn ngữ

            # Thêm bank_code nếu được chỉ định
            if bank_code:
                vnp.requestData['vnp_BankCode'] = bank_code

            # Thêm thông tin thời gian và IP
            vnp.requestData['vnp_CreateDate'] = datetime.now().strftime('%Y%m%d%H%M%S')
            vnp.requestData['vnp_IpAddr'] = ipaddr
            vnp.requestData['vnp_ReturnUrl'] = settings.VNPAY_RETURN_URL  # URL callback sau khi thanh toán

            # Tạo URL thanh toán với chữ ký bảo mật
            vnpay_payment_url = vnp.get_payment_url(settings.VNPAY_PAYMENT_URL, settings.VNPAY_HASH_SECRET)

            # Trả về URL thanh toán và thông tin đơn hàng
            return Response({
                'payment_url': vnpay_payment_url,
                'order_id': order_id,
                'amount': amount
            }, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({
                'error': 'Lỗi khi tạo thanh toán',
                'details': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['get'], url_path='return')
    def payment_return(self, request):
        """
        Xử lý kết quả trả về từ VNPay sau khi thanh toán
        Quy trình:
        1. Nhận các tham số trả về từ VNPay (vnp_TxnRef, vnp_ResponseCode, etc.)
        2. Kiểm tra tính hợp lệ của dữ liệu bằng cách verify chữ ký
        3. Kiểm tra mã phản hồi (vnp_ResponseCode)
        4. Trả về kết quả thanh toán cho client
        """
        # Lấy tất cả tham số từ request GET
        inputData = request.GET
        if inputData:
            # Khởi tạo đối tượng VNPay để xử lý response
            vnp = vnpay()
            vnp.responseData = inputData.dict()

            # Lấy các thông tin từ response
            order_id = inputData['vnp_TxnRef']  # Mã đơn hàng
            amount = int(inputData['vnp_Amount']) / 100  # Số tiền (chia 100 để lấy số tiền thực)
            order_desc = inputData['vnp_OrderInfo']  # Mô tả đơn hàng
            vnp_TransactionNo = inputData['vnp_TransactionNo']  # Mã giao dịch VNPay
            vnp_ResponseCode = inputData['vnp_ResponseCode']  # Mã phản hồi
            vnp_TmnCode = inputData['vnp_TmnCode']  # Mã website tại VNPay
            vnp_PayDate = inputData['vnp_PayDate']  # Thời gian thanh toán
            vnp_BankCode = inputData['vnp_BankCode']  # Mã ngân hàng
            vnp_CardType = inputData['vnp_CardType']  # Loại thẻ

            # Kiểm tra tính hợp lệ của response bằng cách verify chữ ký
            if vnp.validate_response(settings.VNPAY_HASH_SECRET):
                # Nếu mã phản hồi là 00 (thành công)
                if vnp_ResponseCode == "00":
                    try:
                        # Tìm payment trong database
                        payment = Payment.objects.get(id=order_id)

                        # Cập nhật trạng thái thanh toán thành COMPLETED
                        payment.status = PaymentStatus.COMPLETED
                        payment.save()

                        # Tạo thông báo cho người thanh toán
                        notification = Notifications.objects.create(
                            receiver=payment.payer,
                            title="Thanh toán thành công",
                            content=f"Thanh toán của bạn cho phòng {payment.room.room_name} đã được xác nhận thành công",
                            notification_type=NotificationType.PAYMENT,
                            related_object_id=payment.id
                        )

                        # Tạo thông báo cho chủ nhà
                        notification = Notifications.objects.create(
                            receiver=payment.room.motel.user,
                            title="Thanh toán thành công",
                            content=f"Đã nhận thanh toán cho phòng {payment.room.room_name} từ {payment.payer.username}",
                            notification_type=NotificationType.PAYMENT,
                            related_object_id=payment.id
                        )

                    except Payment.DoesNotExist:
                        logger.error(f"Không tìm thấy payment với order_id: {order_id}")

                    # Trả về thông tin thanh toán thành công
                    return Response({
                        "status": "success",
                        "message": "Thanh toán thành công",
                        "data": {
                            "order_id": order_id,
                            "amount": amount,
                            "order_desc": order_desc,
                            "vnp_TransactionNo": vnp_TransactionNo,
                            "vnp_ResponseCode": vnp_ResponseCode,
                            "vnp_BankCode": vnp_BankCode,
                            "vnp_CardType": vnp_CardType,
                            "vnp_PayDate": vnp_PayDate
                        }
                    }, status=status.HTTP_200_OK)

                else:
                    try:
                        # Tìm payment trong database
                        payment = Payment.objects.get(id=order_id)

                        # Cập nhật trạng thái thanh toán thành FAILED
                        payment.status = PaymentStatus.FAILED
                        payment.save()

                        # Tạo thông báo cho người thanh toán
                        notification = Notifications.objects.create(
                            receiver=payment.payer,
                            title="Thanh toán thất bại",
                            content=f"Thanh toán của bạn cho phòng {payment.room.room_name} đã thất bại",
                            notification_type=NotificationType.PAYMENT,
                            related_object_id=payment.id
                        )

                    except Payment.DoesNotExist:
                        logger.error(f"Không tìm thấy payment với order_id: {order_id}")

                    # Trả về thông tin thanh toán thất bại
                    return Response({
                        "status": "error",
                        "message": "Thanh toán thất bại",
                        "data": {
                            "order_id": order_id,
                            "amount": amount,
                            "order_desc": order_desc,
                            "vnp_TransactionNo": vnp_TransactionNo,
                            "vnp_ResponseCode": vnp_ResponseCode
                        }
                    }, status=status.HTTP_400_BAD_REQUEST)
            else:
                # Nếu chữ ký không hợp lệ
                return Response({
                    "status": "error",
                    "message": "Sai checksum (chữ ký không hợp lệ)",
                    "data": {
                        "order_id": order_id,
                        "amount": amount,
                        "order_desc": order_desc,
                        "vnp_TransactionNo": vnp_TransactionNo,
                        "vnp_ResponseCode": vnp_ResponseCode
                    }
                }, status=status.HTTP_400_BAD_REQUEST)
        else:
            # Nếu không có dữ liệu trả về
            return Response({
                "status": "error",
                "message": "Không có dữ liệu"
            }, status=status.HTTP_400_BAD_REQUEST)


class GoogleAuthView(APIView):
    # Cho phép tất cả người dùng truy cập API này mà không cần xác thực
    permission_classes = [AllowAny]

    @staticmethod
    def generate_token(length=32):
        """
        Tạo token ngẫu nhiên với độ dài cho trước
        length: Độ dài của token (mặc định 32 ký tự)
        Chuỗi token ngẫu nhiên gồm chữ cái và số
        """
        # Tạo chuỗi ngẫu nhiên từ các ký tự chữ cái và số với độ dài được chỉ định
        return ''.join(random.choices(string.ascii_letters + string.digits, k=length))

    def post(self, request):
        try:
            # Lấy token_id từ request data
            token_id = request.data.get('token_id')

            # Kiểm tra xem token_id có được cung cấp không
            if not token_id:
                return Response({'error': 'Token ID is required'}, status=status.HTTP_400_BAD_REQUEST)

            # Lấy vai trò người dùng từ request data
            role = request.data.get('role')

            # Kiểm tra vai trò có hợp lệ không (chỉ chấp nhận TENANT hoặc LANDLORD)
            if not role or role not in [UserRole.TENANT, UserRole.LANDLORD]:
                return Response({
                    'error': 'Vai trò không hợp lệ. Vui lòng chọn TENANT hoặc LANDLORD'
                }, status=status.HTTP_400_BAD_REQUEST)

            try:
                # Xác thực token với Google OAuth2
                idinfo = id_token.verify_oauth2_token(
                    token_id,
                    grequests.Request(),
                    audience=settings.GOOGLE_CLIENT_ID,
                    clock_skew_in_seconds=10  # Cho phép chênh lệch 10 giây
                )
            except ValueError as e:
                # Xử lý các lỗi xác thực token
                error_msg = str(e)
                if "Token used too early" in error_msg:
                    return Response({
                        'error': 'Lỗi đồng bộ thời gian. Vui lòng thử lại sau.'
                    }, status=status.HTTP_400_BAD_REQUEST)
                elif "Token expired" in error_msg:
                    return Response({
                        'error': 'Token đã hết hạn. Vui lòng đăng nhập lại.'
                    }, status=status.HTTP_400_BAD_REQUEST)
                else:
                    return Response({
                        'error': f'Lỗi xác thực với Google: {error_msg}'
                    }, status=status.HTTP_400_BAD_REQUEST)
            except Exception as e:
                return Response({
                    'error': 'Lỗi xác thực không xác định. Vui lòng thử lại sau.'
                }, status=status.HTTP_400_BAD_REQUEST)

            # Lấy email từ thông tin token
            email = idinfo.get('email')

            # Kiểm tra xem email có tồn tại trong token không
            if not email:
                print("Error: No email in token")
                return Response({'error': 'Email not found in token'}, status=status.HTTP_400_BAD_REQUEST)

            try:
                # Tìm user trong database theo email
                user = User.objects.get(email=email)

                # Kiểm tra vai trò của user có khớp với vai trò yêu cầu không
                if user.role != role:
                    print(f"Error: Role mismatch. User role: {user.role}, Requested role: {role}")
                    return Response({
                        'error': f'Tài khoản của bạn đã được đăng ký với vai trò {user.role}. Vui lòng đăng nhập với vai trò tương ứng.'
                    }, status=status.HTTP_400_BAD_REQUEST)

                # Lấy hoặc tạo bản ghi SocialAccount liên kết user với Google
                social_account, _ = SocialAccount.objects.get_or_create(
                    user=user,
                    provider='google',
                    defaults={'uid': idinfo.get('sub'), 'extra_data': idinfo}
                )
                # Nếu dữ liệu extra_data trên SocialAccount khác với token Google mới nhận
                # Nếu khác (ví dụ thông tin cập nhật như avatar, tên...), thì cập nhật lại để giữ dữ liệu mới nhất.
                if not social_account.extra_data == idinfo:
                    social_account.extra_data = idinfo
                    social_account.save()

            except User.DoesNotExist:
                try:
                    # Tạo user mới nếu chưa tồn tại
                    user = User.objects.create(
                        email=email,
                        username=email.split('@')[0],  # Lấy phần trước @ làm username
                        first_name=idinfo.get('given_name', ''),
                        last_name=idinfo.get('family_name', ''),
                        is_active=True,
                        role=role,
                        password=make_password(None),  # Tạo mật khẩu ngẫu nhiên
                        avatar=idinfo.get('picture', 'https://lh3.googleusercontent.com/a/default-user')
                    )

                    # Tạo profile tương ứng với vai trò
                    if role == UserRole.TENANT:
                        Tenant.objects.create(user=user)
                    elif role == UserRole.LANDLORD:
                        Landlord.objects.create(user=user)

                    # Tạo bản ghi SocialAccount liên kết user với Google
                    SocialAccount.objects.create(
                        user=user,
                        provider='google',
                        uid=idinfo.get('sub'),
                        extra_data=idinfo
                    )
                except Exception as e:
                    raise

            try:
                # Tạo access token cho user
                application = Application.objects.get(client_id=settings.CLIENT_ID)
                access_token = AccessToken.objects.create(
                    user=user,
                    application=application,
                    token=self.generate_token(),
                    expires=timezone.now() + timedelta(days=1),  # Token hết hạn sau 1 ngày
                    scope='read write'
                )
            except Exception as e:
                raise

            # Trả về thông tin user và access token
            return Response({
                'access_token': access_token.token,
                'token_type': 'Bearer',
                'expires_in': 86400,  # Thời gian hết hạn tính bằng giây (1 ngày)
                'user': {
                    'id': user.id,
                    'email': user.email,
                    'first_name': user.first_name,
                    'last_name': user.last_name,
                    'role': user.role,
                }
            })

        except Exception as e:
            # Xử lý các lỗi không xác định
            return Response({
                'error': f'Lỗi server: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
