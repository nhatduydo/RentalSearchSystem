import asyncio
import logging
import random
import string
from datetime import date, datetime, timedelta

import pytz
import requests
from allauth.socialaccount.models import SocialAccount
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from django.conf import settings
from django.contrib.auth.hashers import make_password
from django.db import transaction
from django.db.models import Count, OuterRef, Q, Subquery
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
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import (SAFE_METHODS, AllowAny, IsAdminUser,
                                        IsAuthenticated)
from rest_framework.response import Response
from rest_framework.views import APIView

from . import paginators, serializers
from .email_service import EmailService
from .models import (Admin, Amenity, ChatRoom, Comment, Favorite, Follow,
                     Landlord, LikeComment, LikeMotel, Message, Motel,
                     MotelImage, MotelRating, Notifications, NotificationType,
                     Payment, PaymentMethod, PaymentStatus, Post, PostImage,
                     PostType, Room, RoomImage, RoomTenant, RoomTenantStatus,
                     SearchHistory, Tenant, User, UserRole)
from .permissions import (IsAdmin, IsLandlordOfRoom, IsLandlordOrTenant,
                          IsMotelOwner, IsOwnerOrAdmin, IsOwnerOrReadOnly,
                          IsPaymentOwnerOrMotelOwner)
from .utils import calculate_distance
from .vnpay import vnpay

logger = logging.getLogger(__name__)


def index(request):
    return HttpResponse("HỆ THỐNG HỖ TRỢ TÌM KIẾM NHÀ TRỌ")


class UserViewSet(viewsets.ViewSet,
                  generics.ListAPIView,
                  generics.RetrieveAPIView,
                  generics.CreateAPIView,
                  generics.UpdateAPIView,
                  generics.DestroyAPIView):
    queryset = User.objects.filter(is_active=True)
    serializer_class = serializers.UserSerializer
    pagination_class = paginators.ItemPanigator

    def get_permissions(self):
        if self.action in ['update', 'partial_update', 'destroy']:
            return [IsOwnerOrAdmin()]
        if self.action == 'create':
            return [AllowAny()]
        return [AllowAny()]

    @transaction.atomic  # đảm bảo tính toàn vẹn dữ liệu
    def create(self, request, *args, **kwargs):
        try:
            user_serializer = serializers.UserSerializer(data=request.data)
            if user_serializer.is_valid():
                user = user_serializer.save()
                # user.save()

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

                role_serializers = {
                    "LANDLORD": serializers.LandlordSerializer,
                    "TENANT": serializers.TenantSerializer
                }

                if user.role in role_serializers:
                    profile_serializer = role_serializers[user.role](data=profile_data)
                    profile_serializer.save()
                else:
                    raise Exception(f"Vai trò không hợp lệ: {user.role}")

                return Response(user_serializer.data, status=status.HTTP_201_CREATED)
            return Response(user_serializer.errors)
        except Exception as e:
            transaction.set_rollback(True)
            return Response({'error': str(e)})

    @action(methods=['GET', 'PATCH'], url_path='current-user', detail=False, permission_classes=[permissions.IsAuthenticated])
    def get_Current_user(self, request):
        if request.method.__eq__("PATCH"):
            user = request.user
            for key, value in request.data.items():
                if key in ['first_name', 'last_name']:
                    setattr(user, key, value)
                elif key == 'password':
                    user.set_password(value)
            user.save()

            return Response(serializers.UserSerializer(user).data)
        return Response(serializers.UserSerializer(request.user).data)  # Trường hợp này không sửa gì cả, chỉ đơn giản là trả lại JSON thông tin user đang đăng nhập.

    @action(methods=['PATCH'], url_path='change-password', detail=False, permission_classes=[permissions.IsAuthenticated])
    def change_password(self, request):
        old_password = request.data.get("old_password")
        new_password = request.data.get("new_password")
        confirm_password = request.data.get("confirm_password")

        if not request.user.check_password(old_password):
            return Response({"error": "Mật khẩu cũ không chính xác"})

        if new_password != confirm_password:
            return Response({"error", "Mật khẩu mới không khớp"})

        request.user.set_password(new_password)
        request.user.save()
        return Response({"success": "Thay đổi mật khẩu thành công"})

    # Lấy thông tin chi tiết người dùng theo ID hoặc slug
    def retrieve(self, request, pk=None):
        if pk.isdigit():
            username = get_object_or_404(User, id=pk)
        else:
            username = get_object_or_404(User, slug=pk)

        serializers = self.get_serializer(username)
        return Response(serializers.data)


class MotelViewSet(viewsets.ViewSet, generics.ListCreateAPIView, generics.RetrieveUpdateDestroyAPIView):
    queryset = Motel.objects.filter(active=True)
    serializer_class = serializers.MotelSerializer
    pagination_class = paginators.ItemPanigator

    def get_permissions(self):
        if self.action in ['update', 'partial_update', 'destroy']:
            return [IsOwnerOrAdmin()]
        if self.action == 'create':
            return [IsAuthenticated()]
        if self.action == 'verify':
            return [IsAdminUser()]
        return [AllowAny()]

    @transaction.atomic
    def perform_create(self, serializer):
        motel = serializer.save(user=self.request.user)
        # Tạo thông báo cho người theo dõi
        # followers = Follow.objects.filter(followed_user=self.request.user, active=True)

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

                # Gửi email đồng bộ sử dụng asyncio.run()
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
        motel = serializer.save()
        # Notify followers about the update
        # followers = Follow.objects.filter(followed_user=self.request.user, active=True)
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

    # Lấy thông tin chi tiết nhà trọ theo ID hoặc slug
    def retrieve(self, request, pk=None):
        if pk.isdigit():
            motel = get_object_or_404(Motel, id=pk)
        else:
            motel = get_object_or_404(Motel, slug=pk)

        serializers = self.get_serializer(motel)
        return Response(serializers.data)

    # like (thích) một phòng trọ
    @action(methods=['POST'], detail=True, url_path='like')
    def like_motel(self, request, pk):
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
        return Response(serializers.MotelSerializer(motel, context={'request': request}).data)

    @action(methods=['POST'], detail=True, url_path='favorite')
    def favorite_motel(self, request, pk):
        motel = self.get_object()
        favorite, created = Favorite.objects.get_or_create(user=request.user, motel=motel)
        if not created:
            favorite.active = not favorite.active
        favorite.save()

        # Thông báo cho chủ nhà khi có người thêm/xóa khỏi yêu thích
        if favorite.active:
            Notifications.objects.create(
                receiver=motel.user,
                title="Nhà trọ được yêu thích",
                content=f"{request.user.username} đã thêm nhà trọ {motel.motel_name} vào danh sách yêu thích",
                notification_type=NotificationType.MOTEL_LIKE,
                related_object_id=motel.id
            )

        return Response(serializers.MotelSerializer(motel, context={'request': request}).data)

    @action(methods=['PATCH'], detail=True, url_path='verify')
    def verify(self, request, pk=None):
        if request.user.role != 'ADMIN':
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
                    'error': 'Nhà trọ chưa đủ điều kiện để xác minh'
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

            return Response({
                'motel': self.get_serializer(motel).data,
                'message': 'Xét duyệt nhà trọ thành công'
            })

        except Exception as e:
            logger.error(f"Lỗi khi xét duyệt nhà trọ: {str(e)}")
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )


class MotelRatingViewSet(viewsets.ModelViewSet):
    queryset = MotelRating.objects.filter(active=True)
    serializer_class = serializers.MotelRatingSerializer
    pagination_class = paginators.ItemPanigator
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    # Lấy danh sách đánh giá theo ID nhà trọ
    def get_queryset(self):
        queryset = self.queryset
        motel_id = self.request.query_params.get('motel_id')
        if motel_id:
            queryset = queryset.filter(motel_id=motel_id)
        return queryset.select_related('user', 'motel')

    # Tạo đánh giá mới và gán người dùng hiện tại
    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class RoomViewSet(viewsets.ViewSet, generics.ListCreateAPIView, generics.RetrieveUpdateDestroyAPIView):
    queryset = Room.objects.filter(active=True)
    serializer_class = serializers.RoomSerializer
    pagination_class = paginators.ItemPanigator

    def get_permissions(self):
        if self.action in ['update', 'partial_update', 'destroy']:
            return [IsOwnerOrAdmin()]
        if self.action == 'create':
            return [IsAuthenticated()]
        return [AllowAny()]

    def retrieve(self, request, pk=None):
        if pk.isdigit():
            room = get_object_or_404(Room, id=pk)
        else:
            room = get_object_or_404(Room, slug=pk)
        serializer = self.get_serializer(room)
        return Response(serializer.data)

    def get_queryset(self):
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
                query = query.filter(**filters)
        return query


class RoomTenantViewSet(viewsets.ModelViewSet):
    serializer_class = serializers.RoomTenantSerializer
    permission_classes = [IsAuthenticated]

    def get_permissions(self):
        if self.action in ['accept_request', 'reject_request']:
            return [IsLandlordOfRoom()]  # Chỉ chủ trọ mới được accept/reject
        elif self.action == 'cancel_contract':
            # Cho phép admin, chủ trọ hoặc người thuê cancel contract
            if self.request.user.role == UserRole.ADMIN:
                return [IsAdmin()]
            return [IsLandlordOrTenant()]
        return [IsAuthenticated()]

    def get_queryset(self):
        if getattr(self, 'swagger_fake_view', False):
            return RoomTenant.objects.none()

        user = self.request.user
        queryset = RoomTenant.objects.select_related(
            'room__motel__user',  # Lấy thông tin user của motel
            'tenant__user'        # Lấy thông tin user của tenant
        )

        if user.role == UserRole.ADMIN:
            return queryset
        elif user.role == UserRole.LANDLORD:
            return queryset.filter(room__motel__user=user)
        elif user.role == UserRole.TENANT:
            return queryset.filter(tenant__user=user)
        return RoomTenant.objects.none()

    def perform_create(self, serializer):
        tenant = Tenant.objects.get(user=self.request.user)
        room_tenant = serializer.save(tenant=tenant, status=RoomTenantStatus.PENDING)
        Notifications.objects.create(
            receiver=room_tenant.room.motel.user,
            title="Yêu cầu thuê phòng",
            content=f"Có yêu cầu thuê phòng mới từ {tenant.full_name}",
            notification_type=NotificationType.SYSTEM,
            related_object_id=str(room_tenant.id)
        )

    @action(detail=True, methods=['post'], url_path='accept-request')
    def accept_request(self, request, pk=None):
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
        return Response(serializers.RoomTenantSerializer(room_tenant).data)

    @action(detail=True, methods=['post'], url_path='reject-request')
    def reject_request(self, request, pk=None):
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
        return Response(serializers.RoomTenantSerializer(room_tenant).data)

    @action(detail=True, methods=['post'], url_path='cancel-contract')
    def cancel_contract(self, request, pk=None):
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
        return Response(serializers.RoomTenantSerializer(room_tenant).data)


class LandlordViewSet(viewsets.ViewSet, generics.ListAPIView, generics.RetrieveAPIView, generics.UpdateAPIView):
    queryset = Landlord.objects.filter(active=True).order_by('user_id')
    serializer_class = serializers.LandlordSerializer
    pagination_class = paginators.ItemPanigator
    permission_classes = [AllowAny]

    def get_permissions(self):
        if self.action in ['update', 'partial_update', 'destroy']:
            return [IsOwnerOrAdmin()]
        if self.action == 'create':
            return [IsAuthenticated()]
        return [AllowAny()]

    # Lấy thông tin chi tiết chủ nhà theo ID, username hoặc slug
    def retrieve(self, request, pk=None):
        try:
            if pk.isdigit():
                landlord = get_object_or_404(Landlord, user_id=pk)
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

    # Lấy danh sách chủ nhà với các điều kiện tìm kiếm
    def get_queryset(self):
        query = self.queryset

        if self.action.__eq__('list'):
            user_id = self.request.query_params.get('id')
            if user_id:
                query = query.filter(user_id=user_id)

            search_query = self.request.query_params.get('q')
            if search_query:
                query = query.filter(full_name__icontains=search_query)

            slug_source = self.request.query_params.get('slug_source')
            if slug_source:
                query = query.filter(slug=slug_source)
        return query

    # Cập nhật thông tin chủ nhà
    def update(self, request, *args, **kwargs):
        try:
            pk = kwargs.get('pk')
            if pk.isdigit():
                landlord = get_object_or_404(Landlord, user_id=pk)
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
            serializer.is_valid(raise_exception=True)
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

    # Xác thực chủ nhà (chỉ admin mới có quyền)
    @action(methods=['PATCH'], detail=True, url_path='verify')
    def verify(self, request, pk=None):
        try:
            if pk.isdigit():
                landlord = get_object_or_404(Landlord, user_id=pk)
            else:
                # Tìm theo username hoặc slug
                landlord = get_object_or_404(Landlord, Q(user__username=pk) | Q(slug=pk))

            # Kiểm tra quyền xác thực
            if not request.user.is_staff:
                return Response(
                    {'error': 'Chỉ admin mới có quyền xác thực chủ nhà'},
                    status=status.HTTP_403_FORBIDDEN
                )

            landlord.is_verified = True
            landlord.save()

            # Tạo thông báo cho chủ nhà
            Notifications.objects.create(
                receiver=landlord.user,
                title="Tài khoản đã được xác thực",
                content="Tài khoản chủ nhà của bạn đã được xác thực thành công",
                notification_type=NotificationType.VERIFICATION_SUCCESS,
                related_object_id=landlord.user.id
            )

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
    queryset = Tenant.objects.filter(active=True)
    serializer_class = serializers.TenantSerializer
    pagination_class = paginators.ItemPanigator
    permission_classes = [AllowAny]

    def get_permissions(self):
        if self.action in ['update', 'partial_update', 'destroy']:
            return [IsOwnerOrAdmin()]
        if self.action == 'create':
            return [IsAuthenticated()]
        return [AllowAny()]

    # Lấy thông tin chi tiết người thuê theo ID, username hoặc slug
    def retrieve(self, request, pk=None):
        try:
            if pk.isdigit():
                tenant = get_object_or_404(Tenant, user_id=pk)
            else:
                tenant = get_object_or_404(Tenant, Q(user__username=pk) | Q(slug=pk))

            serializers = self.get_serializer(tenant)
            return Response(serializers.data)
        except Exception as e:
            logger.error(f"Lỗi khi truy xuất người thuê: {str(e)}")
            return Response(
                {"error": f"Không tìm thấy người thuê với thông tin: {pk}"},
                status=status.HTTP_404_NOT_FOUND
            )

    # Lấy danh sách người thuê với các điều kiện tìm kiếm
    def get_queryset(self):
        query = self.queryset

        if self.action.__eq__('list'):
            user_id = self.request.query_params.get('id')
            if user_id:
                query = query.filter(user_id=user_id)

            search_query = self.request.query_params.get('q')
            if search_query:
                query = query.filter(full_name__icontains=search_query)

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

    # Cập nhật thông tin người thuê
    def update(self, request, *args, **kwargs):
        try:
            pk = kwargs.get('pk')
            if pk.isdigit():
                tenant = get_object_or_404(Tenant, user_id=pk)
            else:
                tenant = get_object_or_404(Tenant, Q(user__username=pk) | Q(slug=pk))

            if request.user != tenant.user and not request.user.is_staff:
                return Response(
                    {'error': 'Bạn không có quyền cập nhật thông tin này'},
                    status=status.HTTP_403_FORBIDDEN
                )

            serializer = self.get_serializer(tenant, data=request.data, partial=True)
            serializer.is_valid(raise_exception=True)
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

    # Lấy danh sách phòng đã thuê
    @action(detail=True, methods=['get'], url_path='rooms')
    def get_rented_rooms(self, request, pk=None):
        try:
            if pk.isdigit():
                tenant = get_object_or_404(Tenant, user_id=pk)
            else:
                tenant = get_object_or_404(Tenant, Q(user__username=pk) | Q(slug=pk))

            room_tenants = RoomTenant.objects.filter(
                tenant=tenant,
                active=True
            ).select_related('room', 'room__motel')

            serializer = serializers.RoomTenantSerializer(room_tenants, many=True)
            return Response(serializer.data)
        except Exception as e:
            logger.error(f"Lỗi khi thuê phòng: {str(e)}")
            return Response(
                {"error": f"Không tìm thấy người thuê với thông tin: {pk}"},
                status=status.HTTP_404_NOT_FOUND
            )

    # Lấy lịch sử thanh toán
    @action(detail=True, methods=['get'], url_path='payments')
    def get_payment_history(self, request, pk=None):
        try:
            if pk.isdigit():
                tenant = get_object_or_404(Tenant, user_id=pk)
            else:
                tenant = get_object_or_404(Tenant, Q(user__username=pk) | Q(slug=pk))

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

    # # Lấy danh sách bài đăng đã lưu
    # @action(detail=True, methods=['get'], url_path='saved-posts')
    # def get_saved_posts(self, request, pk=None):
    #     try:
    #         if pk.isdigit():
    #             tenant = get_object_or_404(Tenant, user_id=pk)
    #         else:
    #             tenant = get_object_or_404(Tenant, Q(user__username=pk) | Q(slug=pk))

    #         saved_posts = Post.objects.filter(
    #             likers=tenant.user,
    #             active=True
    #         )

    #         serializer = serializers.PostSerializer(saved_posts, many=True, context={'request': request})
    #         return Response(serializer.data)
    #     except Exception as e:
    #         logger.error(f"Lỗi khi lưu bài viết: {str(e)}")
    #         return Response(
    #             {"error": f"Không tìm thấy người thuê với thông tin: {pk}"},
    #             status=status.HTTP_404_NOT_FOUND
    #         )


class PostViewSet(viewsets.ViewSet, generics.ListCreateAPIView, generics.RetrieveUpdateDestroyAPIView):
    queryset = Post.objects.filter(active=True)
    serializer_class = serializers.PostSerializer
    pagination_class = paginators.ItemPanigator
    permission_classes = [IsAuthenticated, IsOwnerOrReadOnly]

    def get_serializer_class(self):
        if self.action == 'retrieve':
            return serializers.PostDetailSerializer
        return serializers.PostSerializer

    def perform_create(self, serializer):
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

    def perform_update(self, serializer):
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

    # lấy danh sách các bình luận cấp cao nhất
    @action(detail=True, methods=['get'])
    def comments(self, request, pk=None):
        post = self.get_object()
        comments = Comment.objects.filter(post=post, parent=None)
        serializer = serializers.CommentSerializer(comments, many=True)
        return Response(serializer.data)

    # API endpoint để xóa một hình ảnh cụ thể
    @action(detail=True, methods=['delete'], url_path='images/(?P<image_id>[^/.]+)')
    def delete_image(self, request, pk=None, image_id=None):
        try:
            post = self.get_object()
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
    queryset = Comment.objects.filter(active=True)
    permission_classes = [IsOwnerOrReadOnly]
    serializer_class = serializers.CommentSerializer
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
        serializer = serializers.CommentSerializer(data=data, context={'request': request})
        serializer.is_valid(raise_exception=True)
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

        return Response(serializer.data, status=status.HTTP_201_CREATED)


class VNPayViewSet(viewsets.ViewSet):
    """
    ViewSet xử lý các giao dịch thanh toán qua cổng thanh toán VNPay
    Bao gồm 2 chức năng chính:
    1. Tạo URL thanh toán VNPay
    2. Xử lý kết quả trả về từ VNPay sau khi thanh toán
    """

    def get_client_ip(self, request):
        """
        Lấy địa chỉ IP của client gửi request
        - Kiểm tra header X-Forwarded-For trước (thường được set bởi proxy/load balancer)
        - Nếu không có thì lấy từ REMOTE_ADDR
        """
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]  # Lấy IP đầu tiên trong danh sách
        else:
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

        Request data cần có:
        - order_id: Mã đơn hàng
        - amount: Số tiền thanh toán
        - order_desc: Mô tả đơn hàng (optional)
        - order_type: Loại đơn hàng (optional)
        - bank_code: Mã ngân hàng (optional)
        - language: Ngôn ngữ (optional, mặc định 'vn')
        """
        try:
            # Lấy dữ liệu từ request
            data = request.data
            order_id = data.get('order_id')
            amount = data.get('amount')
            order_desc = data.get('order_desc', 'Thanh toan phong tro')
            order_type = data.get('order_type', 'other')
            bank_code = data.get('bank_code', '')
            language = data.get('language', 'vn')

            # Lấy IP của client
            ipaddr = self.get_client_ip(request)

            # Khởi tạo đối tượng VNPay và set các thông tin cần thiết
            vnp = vnpay()
            vnp.requestData['vnp_Version'] = '2.1.0'  # Phiên bản API
            vnp.requestData['vnp_Command'] = 'pay'    # Lệnh thanh toán
            vnp.requestData['vnp_TmnCode'] = settings.VNPAY_TMN_CODE  # Mã website tại VNPAY
            vnp.requestData['vnp_Amount'] = amount * 100  # Số tiền * 100 (VNPay yêu cầu)
            vnp.requestData['vnp_CurrCode'] = 'VND'   # Đơn vị tiền tệ
            vnp.requestData['vnp_TxnRef'] = order_id  # Mã đơn hàng
            vnp.requestData['vnp_OrderInfo'] = order_desc  # Mô tả đơn hàng
            vnp.requestData['vnp_OrderType'] = order_type  # Loại đơn hàng
            vnp.requestData['vnp_Locale'] = language  # Ngôn ngữ

            # Thêm mã ngân hàng nếu có
            if bank_code:
                vnp.requestData['vnp_BankCode'] = bank_code

            # Thêm thời gian tạo và IP
            vnp.requestData['vnp_CreateDate'] = datetime.now().strftime('%Y%m%d%H%M%S')
            vnp.requestData['vnp_IpAddr'] = ipaddr
            vnp.requestData['vnp_ReturnUrl'] = settings.VNPAY_RETURN_URL  # URL callback sau khi thanh toán

            # Tạo URL thanh toán với chữ ký bảo mật
            vnpay_payment_url = vnp.get_payment_url(settings.VNPAY_PAYMENT_URL, settings.VNPAY_HASH_SECRET)

            return Response({
                'payment_url': vnpay_payment_url,
                'order_id': order_id,
                'amount': amount
            }, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['get'], url_path='return')
    def payment_return(self, request):
        """
        Xử lý kết quả trả về từ VNPay sau khi thanh toán
        Quy trình:
        1. Nhận các tham số trả về từ VNPay (vnp_TxnRef, vnp_ResponseCode, etc.)
        2. Kiểm tra tính hợp lệ của dữ liệu bằng cách verify chữ ký
        3. Kiểm tra mã phản hồi (vnp_ResponseCode)
        4. Trả về kết quả thanh toán cho client

        Các tham số quan trọng từ VNPay:
        - vnp_TxnRef: Mã đơn hàng
        - vnp_Amount: Số tiền
        - vnp_ResponseCode: Mã phản hồi (00: thành công, khác 00: thất bại)
        - vnp_TransactionNo: Mã giao dịch tại VNPay
        - vnp_BankCode: Mã ngân hàng thanh toán
        - vnp_PayDate: Thời gian thanh toán
        """
        inputData = request.GET
        if inputData:
            vnp = vnpay()
            vnp.responseData = inputData.dict()
            order_id = inputData['vnp_TxnRef']
            amount = int(inputData['vnp_Amount']) / 100  # Chia 100 để lấy số tiền thực
            order_desc = inputData['vnp_OrderInfo']
            vnp_TransactionNo = inputData['vnp_TransactionNo']
            vnp_ResponseCode = inputData['vnp_ResponseCode']
            vnp_TmnCode = inputData['vnp_TmnCode']
            vnp_PayDate = inputData['vnp_PayDate']
            vnp_BankCode = inputData['vnp_BankCode']
            vnp_CardType = inputData['vnp_CardType']

            # Verify chữ ký để đảm bảo dữ liệu không bị giả mạo
            if vnp.validate_response(settings.VNPAY_HASH_SECRET):
                if vnp_ResponseCode == "00":  # Thanh toán thành công
                    try:
                        # Tìm payment tương ứng với order_id
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

                else:  # Thanh toán thất bại
                    try:
                        # Tìm payment tương ứng với order_id
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
            else:  # Chữ ký không hợp lệ
                return Response({
                    "status": "error",
                    "message": "Sai checksum",
                    "data": {
                        "order_id": order_id,
                        "amount": amount,
                        "order_desc": order_desc,
                        "vnp_TransactionNo": vnp_TransactionNo,
                        "vnp_ResponseCode": vnp_ResponseCode
                    }
                }, status=status.HTTP_400_BAD_REQUEST)
        else:  # Không có dữ liệu trả về
            return Response({
                "status": "error",
                "message": "Không có dữ liệu"
            }, status=status.HTTP_400_BAD_REQUEST)


class SearchViewSet(viewsets.ViewSet):
    def list(self, request):
        search_query = request.query_params.get('q')
        if search_query:
            motels = Motel.objects.filter(
                Q(motel_name__icontains=search_query) |
                Q(description__icontains=search_query)
            )
        else:
            motels = Motel.objects.all()

            district = request.query_params.get('district')
            if district:
                motels = motels.filter(district__icontains=district)

            city = request.query_params.get('city')
            if city:
                motels = motels.filter(city__icontains=city)

            province = request.query_params.get('province')
            if province:
                motels = motels.filter(province__icontains=province)

            min_price = request.query_params.get('min_price')
            max_price = request.query_params.get('max_price')
            if min_price or max_price:
                post_query = Post.objects.filter(motel=OuterRef('pk'))  # tham chiếu đến pk của bảng Motel
                # Tạo một subquery để lấy các Post có motel_id bằng với pk của Motel
                if min_price:
                    post_query = post_query.filter(min_price__gte=min_price)
                if max_price:
                    post_query = post_query.filter(max_price__lte=max_price)
                motels = motels.filter(id__in=Subquery(post_query.values('motel_id')))
                # Subquery nhúng một query bên trong một query khác

                # # Cách 1: Không dùng Subquery (sẽ tạo nhiều query)
                # post_ids = Post.objects.values_list('motel_id', flat=True)  # Query 1
                # motels = Motel.objects.filter(id__in=post_ids)  # Query 2

                # # Cách 2: Dùng Subquery (chỉ 1 query)
                # motels = Motel.objects.filter(
                #     id__in=Subquery(Post.objects.values('motel_id'))
                # )

            max_people = request.query_params.get('max_people')
            if max_people:
                room_query = Room.objects.filter(motel=OuterRef('pk'), max_people__lte=max_people)
                motels = motels.filter(id__in=Subquery(room_query.values('motel_id')))

            # Serialize và trả về kết quả
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
            latitude = float(request.query_params.get('latitude'))
            longitude = float(request.query_params.get('longitude'))
            radius = float(request.query_params.get('radius', 5))  # Mặc định 5km nếu không có radius

            # Kiểm tra giá trị hợp lệ
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
                distance = calculate_distance(
                    latitude,
                    longitude,
                    motel.latitude,
                    motel.longitude
                )
                if distance <= radius:
                    motel.distance = distance  # Thêm khoảng cách vào object
                    nearby_motels.append(motel)

            # Sắp xếp theo khoảng cách
            nearby_motels.sort(key=lambda x: x.distance)

            # Phân trang sử dụng ItemPanigator
            paginator = paginators.ItemPanigator()
            result_page = paginator.paginate_queryset(nearby_motels, request)

            # Serialize kết quả
            serializer = serializers.MotelSerializer(result_page, many=True, context={'request': request})

            # Thêm khoảng cách vào kết quả
            response_data = serializer.data
            for i, motel in enumerate(result_page):
                response_data[i]['distance'] = round(motel.distance, 2)

            logger.info(f"Tìm kiếm nhà trọ gần vị trí: {latitude}, {longitude}")
            return paginator.get_paginated_response(response_data)

        except (ValueError, TypeError):
            return Response(
                {"error": "Tham số không hợp lệ"},
                status=400
            )
        except Exception as e:
            logger.error(f"Lỗi khi tìm kiếm nhà trọ: {str(e)}")
            return Response(
                {"error": "Có lỗi xảy ra khi tìm kiếm"},
                status=500
            )


class SearchHistoryViewSet(viewsets.ModelViewSet):
    serializer_class = serializers.SearchHistorySerializer
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = paginators.ItemPanigator

    def get_queryset(self):
        if getattr(self, 'swagger_fake_view', False):
            return SearchHistory.objects.none()
        return SearchHistory.objects.filter(
            user=self.request.user,
            active=True
        ).order_by('-created_date')

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        instance.active = False
        instance.save()
        return Response(status=status.HTTP_204_NO_CONTENT)


class NotificationViewSet(viewsets.ViewSet, generics.ListAPIView, generics.RetrieveAPIView, generics.DestroyAPIView):
    queryset = Notifications.objects.filter(active=True)
    permission_classes = [IsAuthenticated]
    serializer_class = serializers.NotificationSerializer
    pagination_class = paginators.ItemPanigator

    def get_queryset(self):
        if getattr(self, 'swagger_fake_view', False):
            return Notifications.objects.none()
        return Notifications.objects.filter(receiver=self.request.user, active=True).order_by('-created_date')

    def perform_destroy(self, instance):
        instance.active = False
        instance.save()

    # lấy danh sách thông báo chưa đọc
    @action(detail=False, methods=['get'], url_path='unread')
    def unread(self, request):
        notifications = self.get_queryset().filter(is_read=False)
        serializer = self.serializer_class(notifications, many=True)
        return Response(serializer.data)

    # Đánh dấu một thông báo là đã đọc
    @action(detail=True, methods=['put'], url_path='read')
    def read(self, request, pk=None):
        try:
            notification = self.get_object()
            notification.is_read = True
            notification.save()
            return Response({'message': 'Thông báo được đánh dấu là đã đọc'})
        except Notifications.DoesNotExist:
            return Response({'error': 'Không tìm thấy thông báo'}, status=status.HTTP_200_OK)

    # Đánh dấu tất cả thông báo là đã đọc
    @action(detail=False, methods=['put'], url_path='read_all')
    def read_all(self, request):
        self.get_queryset().filter(is_read=False).update(is_read=True)
        return Response({'message': 'Tất cả thông báo được đánh dấu là đã đọc'})

    # Xóa tất cả thông báo
    @action(detail=False, methods=['delete'], url_path='delete_all')
    def delete_all(self, request):
        self.get_queryset().update(active=False)
        return Response({'message': 'Tất cả thông báo đã bị xóa'})

    # Đếm số thông báo chưa đọc
    @action(detail=False, methods=['get'], url_path='unread_count')
    def unread_count(self, request):
        count = self.get_queryset().filter(is_read=False).count()
        return Response({'unread_count': count})

    # Lọc thông báo theo loại
    @action(detail=False, methods=['get'], url_path='by_type')
    def by_type(self, request):
        notification_type = request.query_params.get('type')
        if not notification_type:
            return Response({'error': 'Notification type là bắt buộc'}, status=status.HTTP_400_BAD_REQUEST)

        notifications = self.get_queryset().filter(notification_type=notification_type)
        serializer = self.serializer_class(notifications, many=True)
        return Response(serializer.data)


class ChatRoomViewSet(viewsets.ModelViewSet):
    serializer_class = serializers.ChatRoomSerializer
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = paginators.ItemPanigator

    def get_queryset(self):
        if getattr(self, 'swagger_fake_view', False):
            return ChatRoom.objects.none()
        return self.request.user.chat_rooms.filter(active=True).order_by('-updated_date')

    def perform_create(self, serializer):
        chat_room = serializer.save()
        chat_room.participants.add(self.request.user)
        participants = self.request.data.get('participants', [])
        for participant_id in participants:
            try:
                user = User.objects.get(id=participant_id)
                chat_room.participants.add(user)
            except User.DoesNotExist:
                continue


class MessageViewSet(viewsets.ViewSet, generics.ListCreateAPIView, generics.RetrieveUpdateDestroyAPIView):
    serializer_class = serializers.MessageSerializer
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = paginators.ItemPanigator

    def get_queryset(self):
        chat_room_id = self.kwargs.get('chat_room_id')
        return Message.objects.filter(chat_room_id=chat_room_id, active=True).order_by('created_date')

    def perform_create(self, serializer):
        chat_room_id = self.kwargs.get('chat_room_id')
        try:
            chat_room = ChatRoom.objects.get(id=chat_room_id)
            if self.request.user not in chat_room.participants.all():
                raise PermissionDenied("Bạn không có quyền gửi tin nhắn trong phòng chat này")
            # Lưu tin nhắn mới với người gửi là user hiện tại, gán vào phòng chat đó.
            message = serializer.save(sender=self.request.user, chat_room=chat_room)

            # Broadcast tin nhắn qua WebSocket
            # Gửi bản tin mới đến các user đang kết nối vào nhóm chat_<ID phòng> trên WebSocket, Sử dụng Django Channels.
            channel_layer = get_channel_layer()
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
        message = serializer.instance
        if message.sender != self.request.user:
            raise PermissionDenied("Bạn không có quyền chỉnh sửa tin nhắn này")
        message = serializer.save()

        # Broadcast cập nhật tin nhắn qua WebSocket
        channel_layer = get_channel_layer()
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
        if instance.sender != self.request.user:
            raise PermissionDenied("Bạn không có quyền xóa tin nhắn này")
        chat_room_id = instance.chat_room.id
        instance.active = False
        instance.save()

        # Broadcast xóa tin nhắn qua WebSocket
        channel_layer = get_channel_layer()
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
        message = self.get_object()
        message.is_read = True
        message.save()

        # Broadcast trạng thái đã đọc qua WebSocket
        channel_layer = get_channel_layer()
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


class FollowViewSet(viewsets.ViewSet, generics.ListAPIView, generics.CreateAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = serializers.FollowSerializer
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

    def destroy(self, request, pk=None):
        """
        Hủy theo dõi một người dùng
        """
        try:
            follow = Follow.objects.get(
                followed_user_id=pk,
                follower_user=request.user
            )
            follow.active = False
            follow.save()
            return Response(status=status.HTTP_204_NO_CONTENT)
        except Follow.DoesNotExist:
            return Response({"error": "Không tìm thấy mối quan hệ theo dõi"}, status=status.HTTP_404_NOT_FOUND)


class PaymentViewSet(viewsets.ViewSet, generics.ListCreateAPIView, generics.RetrieveUpdateDestroyAPIView):
    serializer_class = serializers.PaymentSerializer
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = paginators.ItemPanigator

    def get_permissions(self):
        if self.action in ['list', 'create']:
            return [permissions.IsAuthenticated()]
        elif self.action in ['retrieve', 'update', 'partial_update', 'destroy', 'update_status']:
            return [permissions.IsAuthenticated(), IsPaymentOwnerOrMotelOwner()]
        return [permissions.IsAuthenticated()]

    def get_queryset(self):
        # Kiểm tra xem có phải là swagger view không
        if getattr(self, 'swagger_fake_view', False):
            return Payment.objects.none()

        # Kiểm tra xem user có được xác thực không
        if not self.request.user.is_authenticated:
            return Payment.objects.none()

        queryset = Payment.objects.filter(active=True).select_related(
            'payer',
            'room',
            'room__motel',
            'room__motel__user'
        )
        user = self.request.user

        # Admin có thể xem tất cả payment
        if user.is_staff:
            return queryset

        # Chủ trọ có thể xem payments của các phòng trong nhà trọ của họ
        if user.role == UserRole.LANDLORD:
            return queryset.filter(room__motel__user=user)

        # Người thuê chỉ có thể xem payments của họ
        return queryset.filter(payer=user)

    def perform_create(self, serializer):
        payment = serializer.save(payer=self.request.user)

        # Thông báo cho chủ nhà khi có thanh toán mới
        Notifications.objects.create(
            receiver=payment.room.motel.user,
            title="Thanh toán mới",
            content=f"Có thanh toán mới cho phòng {payment.room.room_name} từ {self.request.user.username}",
            notification_type=NotificationType.PAYMENT,
            related_object_id=payment.id
        )

    def perform_update(self, serializer):
        payment = serializer.save()

        # Thông báo cho người thanh toán khi có cập nhật
        Notifications.objects.create(
            receiver=payment.payer,
            title="Cập nhật thanh toán",
            content=f"Thanh toán của bạn cho phòng {payment.room.room_name} đã được cập nhật",
            notification_type=NotificationType.PAYMENT,
            related_object_id=payment.id
        )

    # cập nhập trạng thái thanh toán
    @action(detail=True, methods=['patch'], url_path='update-status')
    def update_status(self, request, pk=None):
        payment = self.get_object()
        new_status = request.data.get('status')

        valid_statuses = []
        for choice in PaymentStatus.choices:
            status_code = choice[0]  # phần tử đầu tiên trong tuple (code, label)
            valid_statuses.append(status_code)
        if new_status not in valid_statuses:
            raise ValidationError({
                "error": "Trạng thái không hợp lệ",
                "detail": f"Trạng thái phải là một trong các giá trị: {valid_statuses}"
            })

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

        # Thông báo cho chủ nhà nếu trạng thái là COMPLETED hoặc FAILED
        if new_status in [PaymentStatus.COMPLETED, PaymentStatus.FAILED]:
            status_text = "thành công" if new_status == PaymentStatus.COMPLETED else "thất bại"
            Notifications.objects.create(
                receiver=payment.room.motel.user,
                title=f"Thanh toán {status_text}",
                content=f"Thanh toán cho phòng {payment.room.room_name} từ {payment.payer.username} đã {status_text}",
                notification_type=NotificationType.PAYMENT,
                related_object_id=payment.id
            )

        serializer = self.get_serializer(payment)
        return Response(serializer.data)

    def perform_destroy(self, instance):
        user = self.request.user
        if not (user.is_staff or instance.room.motel in user.motels.all()):
            raise PermissionDenied("Chỉ admin hoặc chủ nhà mới được phép xóa thanh toán")
        instance.active = False
        instance.save()

    #  lấy danh sách các thanh toán của một phòng (room) cụ thể.
    @action(detail=False, methods=['get'], url_path='room/(?P<room_id>[^/.]+)')
    def room_payments(self, request, room_id=None):
        try:
            room = Room.objects.get(id=room_id)
            # Kiểm tra quyền xem thanh toán của phòng
            if not (request.user.is_staff or request.user == room.motel.user):
                return Response(
                    {'error': 'Không có quyền xem thanh toán của phòng này'},
                    status=status.HTTP_403_FORBIDDEN
                )
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
        valid_statuses = []
        for choice in PaymentStatus.choices:
            status_code = choice[0]  # phần tử đầu tiên trong tuple (code, label)
            valid_statuses.append(status_code)
        if status not in valid_statuses:
            return Response(
                {'error': 'Trạng thái không hợp lệ'},
                status=status.HTTP_404_NOT_FOUND
            )

        # Sử dụng get_queryset để lấy payments theo quyền của user
        payments = self.get_queryset().filter(status=status)
        serializer = self.get_serializer(payments, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'], url_path='method/(?P<method>[^/.]+)')
    def method_payments(self, request, method=None):
        valid_methods = []
        for choice in PaymentMethod.choices:
            method_code = choice[0]
            valid_methods.append(method_code)
        if method not in valid_methods:
            return Response(
                {'error': 'Phương thức thanh toán không hợp lệ'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Sử dụng get_queryset để lấy payments theo quyền của user
        payments = self.get_queryset().filter(payment_method=method)
        serializer = self.get_serializer(payments, many=True)
        return Response(serializer.data)


class RoomImageViewSet(viewsets.ModelViewSet):
    queryset = RoomImage.objects.filter(active=True)
    serializer_class = serializers.RoomImageSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [IsOwnerOrAdmin()]
        return [permissions.AllowAny()]

    def get_queryset(self):
        queryset = RoomImage.objects.filter(active=True)
        room_id = self.request.query_params.get('room_id', None)
        if room_id is not None:
            queryset = queryset.filter(room_id=room_id)
        return queryset

    def create(self, request, *args, **kwargs):
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
        instance.active = False
        instance.save()


class MotelImageViewSet(viewsets.ModelViewSet):
    serializer_class = serializers.MotelImageSerializer
    permission_classes = [permissions.IsAuthenticated]
    queryset = MotelImage.objects.filter(active=True)

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


class AmenityViewSet(viewsets.ModelViewSet):
    queryset = Amenity.objects.filter(active=True)
    serializer_class = serializers.AmenitySerializer

    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [IsOwnerOrAdmin()]
        return [AllowAny()]

    def perform_destroy(self, instance):
        instance.active = False
        instance.save()


class FavoriteViewSet(viewsets.ViewSet, generics.ListAPIView):
    serializer_class = serializers.FavoriteSerializer
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = paginators.ItemPanigator

    def get_queryset(self):
        return self.request.user.favorites.filter(active=True)


class StatisticsViewSet(viewsets.ViewSet):
    permission_classes = [permissions.IsAdminUser]

    def _parse_date(self, date_str):
        if not date_str:
            return None
        try:
            # Phân tích chuỗi ngày và làm cho nó nhận biết múi giờ
            naive_dt = datetime.strptime(date_str, '%Y-%m-%d')
            return timezone.make_aware(naive_dt, timezone=pytz.UTC)
        except ValueError:
            return None

    @action(detail=False, methods=['get'], url_path='landlords')
    def landlord_count(self, request):
        """
        Thống kê số lượng chủ trọ theo ngày, tháng, năm, quý.
        Truyền params: type=[day|month|year|quarter], from, to (yyyy-mm-dd)
        """
        from_date = self._parse_date(request.query_params.get('from'))
        to_date = self._parse_date(request.query_params.get('to'))
        type_ = request.query_params.get('type', 'month')
        queryset = Landlord.objects.all()
        if from_date:
            queryset = queryset.filter(created_date__gte=from_date)
        if to_date:
            queryset = queryset.filter(created_date__lte=to_date)
        if type_ == 'day':
            data = queryset.extra({'day': "DATE(created_date)"}).values('day').annotate(count=Count('user_id')).order_by('day')
        elif type_ == 'month':
            data = queryset.extra({'month': "DATE_FORMAT(created_date, '%%Y-%%m')"}).values('month').annotate(count=Count('user_id')).order_by('month')
        elif type_ == 'year':
            data = queryset.extra({'year': "DATE_FORMAT(created_date, '%%Y')"}).values('year').annotate(count=Count('user_id')).order_by('year')
        elif type_ == 'quarter':
            data = queryset.extra({
                'year': "DATE_FORMAT(created_date, '%%Y')",
                'quarter': "QUARTER(created_date)"
            }).values('year', 'quarter').annotate(count=Count('user_id')).order_by('year', 'quarter')
        else:
            return Response({'error': 'type phải là day, month, year, quarter'})
        return Response(data)

    @action(detail=False, methods=['get'], url_path='users')
    def user_count(self, request):
        """
        Thống kê số lượng người dùng theo ngày, tháng, năm, quý.
        Truyền params: type=[day|month|year|quarter], from, to (yyyy-mm-dd)
        """
        from_date = self._parse_date(request.query_params.get('from'))
        to_date = self._parse_date(request.query_params.get('to'))
        type_ = request.query_params.get('type', 'month')
        queryset = User.objects.filter(is_active=True)
        if from_date:
            queryset = queryset.filter(created_date__gte=from_date)
        if to_date:
            queryset = queryset.filter(created_date__lte=to_date)
        if type_ == 'day':
            data = queryset.extra({'day': "DATE(created_date)"}).values('day').annotate(count=Count('id')).order_by('day')
        elif type_ == 'month':
            data = queryset.extra({'month': "DATE_FORMAT(created_date, '%%Y-%%m')"}).values('month').annotate(count=Count('id')).order_by('month')
        elif type_ == 'year':
            data = queryset.extra({'year': "DATE_FORMAT(created_date, '%%Y')"}).values('year').annotate(count=Count('id')).order_by('year')
        elif type_ == 'quarter':
            data = queryset.extra({
                'year': "DATE_FORMAT(created_date, '%%Y')",
                'quarter': "QUARTER(created_date)"
            }).values('year', 'quarter').annotate(count=Count('id')).order_by('year', 'quarter')
        else:
            return Response({'error': 'type phải là day, month, year, quarter'})
        return Response(data)


class GoogleAuthView(APIView):
    permission_classes = [AllowAny]

    @staticmethod
    def generate_token(length=32):
        """
        Tạo token ngẫu nhiên với độ dài cho trước
        Args:
            length: Độ dài của token (mặc định 32 ký tự)
        Returns:
            Chuỗi token ngẫu nhiên gồm chữ cái và số
        """
        return ''.join(random.choices(string.ascii_letters + string.digits, k=length))

    # Hàm xử lý POST request để đăng nhập/đăng ký user bằng token Google gửi lên.
    def post(self, request):
        try:
            token_id = request.data.get('token_id')

            if not token_id:
                return Response({'error': 'Token ID is required'}, status=status.HTTP_400_BAD_REQUEST)

            role = request.data.get('role')

            if not role or role not in [UserRole.TENANT, UserRole.LANDLORD]:
                return Response({
                    'error': 'Vai trò không hợp lệ. Vui lòng chọn TENANT hoặc LANDLORD'
                }, status=status.HTTP_400_BAD_REQUEST)

            try:
                idinfo = id_token.verify_oauth2_token(
                    token_id,
                    grequests.Request(),
                    audience=settings.GOOGLE_CLIENT_ID,  # là client ID của app, đảm bảo token đúng ứng dụng.
                    clock_skew_in_seconds=10  # Cho phép chênh lệch 10 giây
                )
            except ValueError as e:
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

            email = idinfo.get('email')

            if not email:
                print("Error: No email in token")
                return Response({'error': 'Email not found in token'}, status=status.HTTP_400_BAD_REQUEST)

            try:
                user = User.objects.get(email=email)

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
                    user = User.objects.create(
                        email=email,
                        username=email.split('@')[0],
                        first_name=idinfo.get('given_name', ''),
                        last_name=idinfo.get('family_name', ''),
                        is_active=True,
                        role=role,
                        password=make_password(None),
                        avatar=idinfo.get('picture', 'https://lh3.googleusercontent.com/a/default-user')
                    )

                    if role == UserRole.TENANT:
                        Tenant.objects.create(user=user)
                    elif role == UserRole.LANDLORD:
                        Landlord.objects.create(user=user)

                    # Tạo bản ghi SocialAccount liên kết user với Google
                    SocialAccount.objects.create(
                        user=user,
                        provider='google',
                        uid=idinfo.get('sub'),    # ID định danh Google user
                        extra_data=idinfo
                    )
                except Exception as e:
                    raise

            try:
                application = Application.objects.get(client_id=settings.CLIENT_ID)
                access_token = AccessToken.objects.create(
                    user=user,
                    application=application,
                    token=self.generate_token(),
                    expires=timezone.now() + timedelta(days=1),
                    scope='read write'
                )
            except Exception as e:
                raise

            return Response({
                'access_token': access_token.token,
                'token_type': 'Bearer',
                'expires_in': 86400,
                'user': {
                    'id': user.id,
                    'email': user.email,
                    'first_name': user.first_name,
                    'last_name': user.last_name,
                    'role': user.role,
                }
            })

        except Exception as e:
            return Response({
                'error': f'Lỗi server: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
