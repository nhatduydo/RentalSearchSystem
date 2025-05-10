import logging
from datetime import datetime

from accommodationSearch import paginators, serializers
from django.conf import settings
from django.contrib.auth import authenticate
from django.db import transaction
from django.db.models import Count, OuterRef, Q, Subquery, Sum
from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.csrf import csrf_exempt
from rest_framework import generics, parsers, permissions, status, viewsets
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.exceptions import NotFound, PermissionDenied
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from unidecode import unidecode

from .forms import PaymentForm
from .models import (Admin, Amenity, ChatRoom, Comment, Favorite, Follow,
                     Landlord, LikeComment, LikeMotel, Message, Motel,
                     MotelImage, MotelRating, Notifications, NotificationType,
                     Payment, PaymentMethod, PaymentStatus, Post, Room,
                     RoomImage, RoomTenant, RoomTenantStatus, SearchHistory,
                     Tenant, User)
from .permissions import IsOwnerOrAdmin, IsOwnerOrReadOnly
from .utils import calculate_distance
from .vnpay import vnpay

logger = logging.getLogger(__name__)


def index(request):
    return HttpResponse("HỆ THỐNG HỖ TRỢ TÌM KIẾM NHÀ TRỌ")

# class AdminViewSet(viewsets.ViewSet, generics.ListAPIView):
#     queryset = Admin.objects.filter(active = True)
#     serializer_class = serializers.AdminSerializer


class UserViewSet(viewsets.ViewSet,
                  generics.ListAPIView,
                  generics.RetrieveAPIView,
                  generics.CreateAPIView,
                  generics.UpdateAPIView,
                  generics.DestroyAPIView):
    queryset = User.objects.filter(is_active=True)
    serializer_class = serializers.UserSerializer
    pagination_class = paginators.ItemPanigator
    parser_classes = [parsers.MultiPartParser, parsers.FormParser, parsers.JSONParser]

    def get_permissions(self):
        if self.action in ['create']:
            return [permissions.AllowAny()]
        return [permissions.IsAuthenticated()]

    @transaction.atomic
    def create(self, request, *args, **kwargs):
        try:
            user_serializer = serializers.UserSerializer(data=request.data)
            if user_serializer.is_valid():
                if 'avatar' in request.data and isinstance(request.data['avatar'], str):
                    user = user_serializer.save()
                else:
                    user = user_serializer.save()
                user.save() 

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
                
                if user.role == "LANDLORD":
                    landlord_serializer = serializers.LandlordSerializer(data=profile_data)
                    if landlord_serializer.is_valid():
                        landlord_serializer.save()
                    else:
                        raise Exception(landlord_serializer.errors)
                elif user.role == "TENANT":
                    tenant_serializer = serializers.TenantSerializer(data=profile_data)
                    if tenant_serializer.is_valid():
                        tenant_serializer.save()
                    else:
                        raise Exception(tenant_serializer.errors)

                return Response(user_serializer.data, status=201)
            return Response(user_serializer.errors, status=400)
        except Exception as e:
            transaction.set_rollback(True)
            return Response({'error': str(e)}, status=400)

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
        return Response(serializers.UserSerializer(request.user).data)

    @action(methods=['PATCH'], url_path='change-password', detail=False, permission_classes=[permissions.IsAuthenticated])
    def change_password(self, request):
        old_password = request.data.get("old_password")
        new_password = request.data.get("new_password")
        confirm_password = request.data.get("confirm_password")

        if not request.user.check_password(old_password):
            return Response({"error": "Mật khẩu cũ không chính xác"}, status=400)

        if new_password != confirm_password:
            return Response({"error", "Mật khẩu mới không khớp"}, status=400)

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
        if self.action in ['like_comment']:
            return [IsAuthenticated()]
        elif self.action in ['update', 'destroy']:
            return [IsOwnerOrReadOnly()]
        return [AllowAny()]

    def perform_create(self, serializer):
        motel = serializer.save()
        
        # Thông báo cho followers khi chủ nhà tạo mới nhà trọ
        followers = Follow.objects.filter(following=self.request.user)
        for follow in followers:
            Notifications.objects.create(
                receiver=follow.followers,
                title="Nhà trọ mới",
                content=f"{self.request.user.username} vừa đăng một nhà trọ mới: {motel.motel_name}",
                notification_type=NotificationType.MOTEL_UPDATE,
                related_object_id=motel.id
            )

    # Lấy thông tin chi tiết nhà trọ theo ID hoặc slug
    def retrieve(self, request, pk=None):
        if pk.isdigit():
            motel = get_object_or_404(Motel, id=pk)
        else:
            motel = get_object_or_404(Motel, slug=pk)

        serializers = self.get_serializer(motel)
        return Response(serializers.data)

    # like (thích) một khách sạn
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
                notification_type=NotificationType.MOTEL_UPDATE,
                related_object_id=motel.id
            )

        return Response(serializers.MotelSerializer(motel, context={'request': request}).data)


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

    # Lấy thông tin chi tiết phòng theo ID hoặc slug
    def retrieve(self, request, pk=None):
        if pk.isdigit():
            room = get_object_or_404(Room, id=pk)
        else:
            room = get_object_or_404(Room, slug=pk)

        serializers = self.get_serializer(room)
        return Response(serializers.data)

    # Lấy danh sách phòng với các điều kiện tìm kiếm
    def get_queryset(self):
        query = self.queryset

        if self.action.__eq__('list'):
            search_query = self.request.query_params.get('q')
            if search_query:
                query = query.filter(room_name__icontains=search_query)

            motel_id = self.request.query_params.get('motel_id')
            if motel_id:
                query = query.filter(motel_id=motel_id)

            motel_slug = self.request.query_params.get('motel_slug')
            if motel_slug:
                motel = get_object_or_404(Motel, slug=motel_slug)
                query = query.filter(motel=motel)
        return query


class RoomTenantViewSet(viewsets.ModelViewSet):
    queryset = RoomTenant.objects.all()
    serializer_class = serializers.RoomTenantSerializer
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = paginators.ItemPanigator

    def get_queryset(self):
        queryset = self.queryset

        if self.action == 'list':
            tenant_id = self.request.query_params.get('tenant_id')
            if tenant_id:
                queryset = queryset.filter(tenant_id=tenant_id)

            room_id = self.request.query_params.get('room_id')
            if room_id:
                queryset = queryset.filter(room_id=room_id)

            status = self.request.query_params.get('status')
            if status:
                queryset = queryset.filter(status=status)

        return queryset.select_related('room', 'tenant')

    def perform_create(self, serializer):
        room_tenant = serializer.save()
        # Thông báo cho chủ nhà khi có yêu cầu thuê phòng mới
        Notifications.objects.create(
            receiver=room_tenant.room.motel.user,
            title="Yêu cầu thuê phòng mới",
            content=f"{self.request.user.username} đã gửi yêu cầu thuê phòng {room_tenant.room.room_name}",
            notification_type=NotificationType.MOTEL_UPDATE,
            related_object_id=room_tenant.id
        )

    @action(detail=True, methods=['put'], url_path='status')
    def update_status(self, request, pk=None):
        room_tenant = self.get_object()
        new_status = request.data.get('status')

        valid_statuses = []
        for status_tuple in RoomTenantStatus.choices:
            status_code = status_tuple[0]
            valid_statuses.append(status_code)

        if new_status not in valid_statuses:
            return Response(
                {'error': 'Trạng thái không hợp lệ'},
                status=status.HTTP_400_BAD_REQUEST
            )

        room_tenant.status = new_status
        room_tenant.save()

        # Thông báo cho người thuê khi trạng thái thay đổi
        Notifications.objects.create(
            receiver=room_tenant.tenant.user,
            title="Cập nhật trạng thái thuê phòng",
            content=f"Trạng thái thuê phòng {room_tenant.room.room_name} đã được cập nhật thành {new_status}",
            notification_type=NotificationType.MOTEL_UPDATE,
            related_object_id=room_tenant.id
        )

        # Thông báo cho chủ nhà khi trạng thái thay đổi
        Notifications.objects.create(
            receiver=room_tenant.room.motel.user,
            title="Cập nhật trạng thái thuê phòng",
            content=f"Trạng thái thuê phòng {room_tenant.room.room_name} đã được cập nhật thành {new_status}",
            notification_type=NotificationType.MOTEL_UPDATE,
            related_object_id=room_tenant.id
        )

        serializer = self.get_serializer(room_tenant)
        return Response(serializer.data)


class LandlordViewSet(viewsets.ViewSet, generics.ListAPIView, generics.RetrieveAPIView, generics.UpdateAPIView):
    queryset = Landlord.objects.filter(active=True)
    serializer_class = serializers.LandlordSerializer
    pagination_class = paginators.ItemPanigator
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    parser_classes = [parsers.MultiPartParser, parsers.FormParser, parsers.JSONParser]

    def get_permissions(self):
        if self.action == 'verify':
            return [permissions.IsAdminUser()]
        return [permissions.IsAuthenticatedOrReadOnly()]

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
            logger.error(f"Lỗi khi tìm chủ nhà: {str(e)}")
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
                notification_type="VERIFICATION",
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
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    parser_classes = [parsers.MultiPartParser, parsers.FormParser, parsers.JSONParser]

    def get_permissions(self):
        if self.action in ['update', 'partial_update']:
            return [permissions.IsAuthenticated()]
        return [permissions.IsAuthenticatedOrReadOnly()]

    # Lấy thông tin chi tiết người thuê theo ID, username hoặc slug
    def retrieve(self, request, pk=None):
        try:
            if pk.isdigit():
                tenant = get_object_or_404(Tenant, user_id=pk)
            else:
                # Tìm theo username hoặc slug
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
                from datetime import date
                today = date.today()
                if min_age:
                    max_date = today.replace(year=today.year - int(min_age))
                    query = query.filter(date_of_birth__lte=max_date)
                if max_age:
                    min_date = today.replace(year=today.year - int(max_age) - 1)
                    query = query.filter(date_of_birth__gt=min_date)

        return query

    # Cập nhật thông tin người thuê
    def update(self, request, *args, **kwargs):
        try:
            pk = kwargs.get('pk')
            if pk.isdigit():
                tenant = get_object_or_404(Tenant, user_id=pk)
            else:
                # Tìm theo username hoặc slug
                tenant = get_object_or_404(Tenant, Q(user__username=pk) | Q(slug=pk))

            # Kiểm tra quyền cập nhật
            if request.user != tenant.user and not request.user.is_staff:
                return Response(
                    {'error': 'Bạn không có quyền cập nhật thông tin này'},
                    status=status.HTTP_403_FORBIDDEN
                )

            # Cập nhật thông tin
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
                # Tìm theo username hoặc slug
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
                # Tìm theo username hoặc slug
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

    # Lấy danh sách bài đăng đã lưu
    @action(detail=True, methods=['get'], url_path='saved-posts')
    def get_saved_posts(self, request, pk=None):
        try:
            if pk.isdigit():
                tenant = get_object_or_404(Tenant, user_id=pk)
            else:
                # Tìm theo username hoặc slug
                tenant = get_object_or_404(Tenant, Q(user__username=pk) | Q(slug=pk))

            saved_posts = Post.objects.filter(
                likers=tenant.user,
                active=True
            )

            serializer = serializers.PostSerializer(saved_posts, many=True, context={'request': request})
            return Response(serializer.data)
        except Exception as e:
            logger.error(f"Lỗi khi lưu bài viết: {str(e)}")
            return Response(
                {"error": f"Không tìm thấy người thuê với thông tin: {pk}"},
                status=status.HTTP_404_NOT_FOUND
            )


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

        if post.post_type == 'RENT_OUT' and post.motel:
            followers = Follow.objects.filter(following=self.request.user)
            for follow in followers:
                Notifications.objects.create(
                    receiver=follow.followers,  # Người nhận thông báo là người theo dõi
                    title="New Post",
                    content=f"{self.request.user.username} đã đăng một bài đăng mới: {post.title}",
                    notification_type="NEW_POST",
                    related_object_id=post.id
                )

    # lấy danh sách các bình luận cấp cao nhất
    @action(detail=True, methods=['get'])
    def comments(self, request, pk=None):
        post = self.get_object()
        comments = Comment.objects.filter(post=post, parent=None)
        serializer = serializers.CommentSerializer(comments, many=True)
        return Response(serializer.data)


class CommentViewSet(viewsets.ViewSet, generics.DestroyAPIView, generics.UpdateAPIView):
    queryset = Comment.objects.filter(active=True)
    permission_classes = [IsOwnerOrReadOnly]
    serializer_class = serializers.CommentSerializer
    pagination_class = paginators.ItemPanigator

    def get_permissions(self):
        if self.action in ['create', 'like_comment', 'reply_comment']:
            return [IsAuthenticated()]
        elif self.action in ['update', 'destroy']:
            return [IsOwnerOrReadOnly()]
        return [AllowAny()]

    # lấy danh sách bình luận (Comment) cho một bài viết cụ thể.
    def list(self, request):
        post_id = request.GET.get('post_id')
        if post_id:
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
                notification_type=NotificationType.NEW_COMMENT,
                related_object_id=comment.id
            )

        return Response(serializers.CommentSerializer(comment, context={'request': request}).data)

    # trả lời một bình luận.
    @action(methods=['POST'], detail=True, url_path='reply')
    def reply_comment(self, request, pk):
        parent = self.get_object()
        data = {
            'post': parent.post.id,
            'user': request.user.id,
            'content': request.data.get('content'),
            'parent': parent.id
        }

        serializer = serializers.CommentSerializer(data=data, context={'request': request})
        serializer.is_valid(raise_exception=True)
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
    # Lấy địa chỉ IP của client gửi request
    def get_client_ip(self, request):
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip

    # Tạo URL thanh toán VNPay và trả về cho client
    @action(detail=False, methods=['post'], url_path='create')
    def create_payment(self, request):
        try:
            # Get data from request
            data = request.data
            order_id = data.get('order_id')
            amount = data.get('amount')
            order_desc = data.get('order_desc', 'Thanh toan don hang')
            order_type = data.get('order_type', 'other')
            bank_code = data.get('bank_code', '')
            language = data.get('language', 'vn')

            # Get client IP
            ipaddr = self.get_client_ip(request)

            # Initialize VNPay
            vnp = vnpay()
            vnp.requestData['vnp_Version'] = '2.1.0'
            vnp.requestData['vnp_Command'] = 'pay'
            vnp.requestData['vnp_TmnCode'] = settings.VNPAY_TMN_CODE
            vnp.requestData['vnp_Amount'] = amount * 100
            vnp.requestData['vnp_CurrCode'] = 'VND'
            vnp.requestData['vnp_TxnRef'] = order_id
            vnp.requestData['vnp_OrderInfo'] = order_desc
            vnp.requestData['vnp_OrderType'] = order_type
            vnp.requestData['vnp_Locale'] = language

            if bank_code:
                vnp.requestData['vnp_BankCode'] = bank_code

            vnp.requestData['vnp_CreateDate'] = datetime.now().strftime('%Y%m%d%H%M%S')
            vnp.requestData['vnp_IpAddr'] = ipaddr
            vnp.requestData['vnp_ReturnUrl'] = settings.VNPAY_RETURN_URL

            # Get payment URL
            vnpay_payment_url = vnp.get_payment_url(settings.VNPAY_PAYMENT_URL, settings.VNPAY_HASH_SECRET)

            return Response({
                'payment_url': vnpay_payment_url,
                'order_id': order_id,
                'amount': amount
            }, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

    # Xử lý kết quả thanh toán từ VNPay và trả về trạng thái giao dịch
    @action(detail=False, methods=['get'], url_path='return')
    def payment_return(self, request):
        inputData = request.GET
        if inputData:
            vnp = vnpay()
            vnp.responseData = inputData.dict()
            order_id = inputData['vnp_TxnRef']
            amount = int(inputData['vnp_Amount']) / 100
            order_desc = inputData['vnp_OrderInfo']
            vnp_TransactionNo = inputData['vnp_TransactionNo']
            vnp_ResponseCode = inputData['vnp_ResponseCode']
            vnp_TmnCode = inputData['vnp_TmnCode']
            vnp_PayDate = inputData['vnp_PayDate']
            vnp_BankCode = inputData['vnp_BankCode']
            vnp_CardType = inputData['vnp_CardType']

            if vnp.validate_response(settings.VNPAY_HASH_SECRET):
                if vnp_ResponseCode == "00":
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
        else:
            return Response({
                "status": "error",
                "message": "Không có dữ liệu"
            }, status=status.HTTP_400_BAD_REQUEST)


class SearchViewSet(viewsets.ViewSet):
    # Tìm kiếm theo nhiều tiêu chí
    def list(self, request):
        # Tìm theo từ khóa
        search_query = request.query_params.get('q')
        if search_query:
            motels = Motel.objects.filter(
                Q(motel_name__icontains=search_query) |
                Q(description__icontains=search_query)
            )
        else:
            motels = Motel.objects.all()

        # Tìm theo địa điểm
        district = request.query_params.get('district')
        if district:
            motels = motels.filter(district__icontains=district)

        city = request.query_params.get('city')
        if city:
            motels = motels.filter(city__icontains=city)

        province = request.query_params.get('province')
        if province:
            motels = motels.filter(province__icontains=province)

        # Tìm theo giá phòng (từ Post)
        min_price = request.query_params.get('min_price')
        max_price = request.query_params.get('max_price')
        if min_price or max_price:
            post_query = Post.objects.filter(motel=OuterRef('pk'))
            if min_price:
                post_query = post_query.filter(min_price__gte=min_price)
            if max_price:
                post_query = post_query.filter(max_price__lte=max_price)
            motels = motels.filter(id__in=Subquery(post_query.values('motel_id')))

        # Tìm theo số người (từ Room)
        max_people = request.query_params.get('max_people')
        if max_people:
            room_query = Room.objects.filter(
                motel=OuterRef('pk'),
                max_people__lte=max_people
            )
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
                    status=400
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

            # Phân trang
            paginator = PageNumberPagination()
            paginator.page_size = 10
            paginator.page_size_query_param = 'page_size'
            paginator.max_page_size = 100
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
        # Xóa mềm - chỉ set active=False
        instance = self.get_object()
        instance.active = False
        instance.save()
        return Response(status=status.HTTP_204_NO_CONTENT)


class NotificationViewSet(viewsets.ViewSet):
    permission_classes = [IsAuthenticated]
    serializer_class = serializers.NotificationSerializer
    pagination_class = paginators.ItemPanigator

    def get_queryset(self):
        if getattr(self, 'swagger_fake_view', False):
            return Notifications.objects.none()
        return Notifications.objects.filter(receiver=self.request.user, active=True)

    # Lấy danh sách tất cả thông báo
    def list(self, request):
        notifications = self.get_queryset().order_by('-created_date')
        paginator = self.pagination_class()
        page = paginator.paginate_queryset(notifications, request)
        if page is not None:
            serializer = self.serializer_class(page, many=True)
            return paginator.get_paginated_response(serializer.data)
        serializer = self.serializer_class(notifications, many=True)
        return Response(serializer.data)

    # Lấy chi tiết một thông báo
    def retrieve(self, request, pk=None):
        try:
            notification = self.get_queryset().get(pk=pk)
            serializer = self.serializer_class(notification)
            return Response(serializer.data)
        except Notifications.DoesNotExist:
            return Response({'error': 'Không tìm thấy thông báo'}, status=status.HTTP_404_NOT_FOUND)

    # Xóa một thông báo
    def destroy(self, request, pk=None):
        try:
            notification = self.get_queryset().get(pk=pk)
            notification.active = False
            notification.save()
            return Response(status=status.HTTP_204_NO_CONTENT)
        except Notifications.DoesNotExist:
            return Response({'error': 'Không tìm thấy thông báo'}, status=status.HTTP_404_NOT_FOUND)

    # lấy danh sách thông báo chưa đọc
    @action(detail=False, methods=['get'], url_path='unread')
    def unread(self, request):
        notifications = self.get_queryset().filter(is_read=False).order_by('-created_date')
        serializer = self.serializer_class(notifications, many=True)
        return Response(serializer.data)

    # Đánh dấu một thông báo là đã đọc
    @action(detail=True, methods=['put'], url_path='read')
    def read(self, request, pk=None):
        try:
            notification = self.get_queryset().get(pk=pk)
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

        notifications = self.get_queryset().filter(notification_type=notification_type).order_by('-created_date')
        serializer = self.serializer_class(notifications, many=True)
        return Response(serializer.data)


class ChatRoomViewSet(viewsets.ModelViewSet):
    serializer_class = serializers.ChatRoomSerializer
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = paginators.ItemPanigator

    def get_queryset(self):
        if getattr(self, 'swagger_fake_view', False):
            return ChatRoom.objects.none()
        return ChatRoom.objects.filter(
            participants=self.request.user,
            active=True
        ).order_by('-updated_date')

    def perform_create(self, serializer):
        chat_room = serializer.save()
        # Thêm người tạo phòng
        chat_room.participants.add(self.request.user)
        # Thêm các participants khác từ request
        participants = self.request.data.get('participants', [])
        for participant_id in participants:
            try:
                user = User.objects.get(id=participant_id)
                chat_room.participants.add(user)
            except User.DoesNotExist:
                continue


class MessageViewSet(viewsets.ModelViewSet):
    serializer_class = serializers.MessageSerializer
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = paginators.ItemPanigator

    def get_queryset(self):
        chat_room_id = self.kwargs.get('chat_room_id')
        return Message.objects.filter(
            chat_room_id=chat_room_id,
            active=True
        ).order_by('created_date')

    def perform_create(self, serializer):
        chat_room_id = self.kwargs.get('chat_room_id')
        try:
            chat_room = ChatRoom.objects.get(id=chat_room_id)
            # Kiểm tra xem người dùng có trong phòng chat không
            if self.request.user not in chat_room.participants.all():
                raise PermissionDenied("Bạn không có quyền gửi tin nhắn trong phòng chat này")
            serializer.save(sender=self.request.user, chat_room=chat_room)
        except ChatRoom.DoesNotExist:
            raise NotFound("Không tìm thấy phòng chat")

    def update(self, request, *args, **kwargs):
        message = self.get_object()
        # Kiểm tra xem người dùng có phải là người gửi tin nhắn không
        if message.sender != request.user:
            raise PermissionDenied("Bạn không có quyền chỉnh sửa tin nhắn này")
        return super().update(request, *args, **kwargs)

    def destroy(self, request, *args, **kwargs):
        message = self.get_object()
        # Kiểm tra xem người dùng có phải là người gửi tin nhắn không
        if message.sender != request.user:
            raise PermissionDenied("Bạn không có quyền xóa tin nhắn này")
        # Xóa mềm tin nhắn
        message.active = False
        message.save()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=True, methods=['put'], url_path='read')
    def read(self, request, chat_room_id=None, pk=None):
        message = self.get_object()
        # Kiểm tra xem người dùng có trong phòng chat không
        if request.user not in message.chat_room.participants.all():
            raise PermissionDenied("Bạn không có quyền đánh dấu tin nhắn này là đã đọc")
        message.is_read = True
        message.save()
        return Response({'status': 'tin nhắn được đánh dấu là đã đọc'})


class FollowViewSet(viewsets.ViewSet):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = serializers.FollowSerializer
    pagination_class = paginators.ItemPanigator

    def get_queryset(self):
        if getattr(self, 'swagger_fake_view', False):
            return Follow.objects.none()
        if not self.request.user.is_authenticated:
            return Follow.objects.none()
        return Follow.objects.filter(followers=self.request.user, active=True)

    def list(self, request):
        """
        Lấy danh sách những người mà người dùng đang theo dõi
        """
        follows = self.get_queryset()
        serializer = self.serializer_class(follows, many=True)
        return Response(serializer.data)

    def create(self, request):
        """
        Theo dõi một người dùng
        """
        following_id = request.data.get('following_id')
        if not following_id:
            return Response({"error": "Thiếu ID người dùng cần theo dõi"}, status=400)

        try:
            following_user = User.objects.get(id=following_id)
        except User.DoesNotExist:
            return Response({"error": "Người dùng không tồn tại"}, status=404)

        if following_user == request.user:
            return Response({"error": "Không thể theo dõi chính mình"}, status=400)

        follow, created = Follow.objects.get_or_create(
            following=following_user,
            followers=request.user
        )

        if not created:
            follow.active = not follow.active
            follow.save()

        serializer = self.serializer_class(follow)
        return Response(serializer.data)

    def destroy(self, request, pk=None):
        """
        Hủy theo dõi một người dùng
        """
        try:
            follow = Follow.objects.get(
                following_id=pk,
                followers=request.user
            )
            follow.active = False
            follow.save()
            return Response(status=status.HTTP_204_NO_CONTENT)
        except Follow.DoesNotExist:
            return Response({"error": "Không tìm thấy mối quan hệ theo dõi"}, status=404)


class PaymentViewSet(viewsets.ModelViewSet):
    queryset = Payment.objects.filter(active=True)
    serializer_class = serializers.PaymentSerializer
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = paginators.ItemPanigator

    def get_queryset(self):
        queryset = self.queryset
        if self.action == 'list':
            queryset = queryset.filter(payer=self.request.user)
        return queryset.select_related('payer', 'room')

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

    @action(detail=False, methods=['get'], url_path='room/(?P<room_id>[^/.]+)')
    def room_payments(self, request, room_id=None):
        try:
            room = Room.objects.get(id=room_id)
            payments = self.get_queryset().filter(room=room)
            serializer = self.get_serializer(payments, many=True)
            return Response(serializer.data)
        except Room.DoesNotExist:
            return Response({'error': 'Phòng không tồn tại'}, status=status.HTTP_404_NOT_FOUND)

    @action(detail=False, methods=['get'], url_path='status/(?P<status>[^/.]+)')
    def status_payments(self, request, status=None):
        valid_statuses = []
        for status_tuple in PaymentStatus.choices:
            status_code = status_tuple[0]
            valid_statuses.append(status_code)

        if status not in valid_statuses:
            return Response({'error': 'Trạng thái không hợp lệ'}, status=status.HTTP_400_BAD_REQUEST)

        payments = self.get_queryset().filter(status=status)
        serializer = self.get_serializer(payments, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'], url_path='method/(?P<method>[^/.]+)')
    def method_payments(self, request, method=None):
        valid_methods = []
        for method_tuple in PaymentMethod.choices:
            method_code = method_tuple[0]
            valid_methods.append(method_code)

        if method not in valid_methods:
            return Response({'error': 'Phương thức thanh toán không hợp lệ'}, status=status.HTTP_400_BAD_REQUEST)

        payments = self.get_queryset().filter(payment_method=method)
        serializer = self.get_serializer(payments, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['patch'], url_path='update-status')
    def update_status(self, request, pk=None):
        payment = self.get_object()
        new_status = request.data.get('status')

        valid_statuses = []
        for status_tuple in PaymentStatus.choices:
            status_code = status_tuple[0]
            valid_statuses.append(status_code)

        if new_status not in valid_statuses:
            return Response({'error': 'Trạng thái không hợp lệ'}, status=status.HTTP_400_BAD_REQUEST)

        payment.status = new_status
        payment.save()

        # Thông báo cho người thanh toán khi trạng thái thay đổi
        if new_status == PaymentStatus.COMPLETED:
            Notifications.objects.create(
                receiver=payment.payer,
                title="Thanh toán thành công",
                content=f"Thanh toán cho phòng {payment.room.room_name} đã hoàn tất",
                notification_type=NotificationType.PAYMENT,
                related_object_id=payment.id
            )
            # Thông báo cho chủ nhà
            Notifications.objects.create(
                receiver=payment.room.motel.user,
                title="Thanh toán thành công",
                content=f"Thanh toán cho phòng {payment.room.room_name} từ {payment.payer.username} đã hoàn tất",
                notification_type=NotificationType.PAYMENT,
                related_object_id=payment.id
            )
        elif new_status == PaymentStatus.FAILED:
            Notifications.objects.create(
                receiver=payment.payer,
                title="Thanh toán thất bại",
                content=f"Thanh toán cho phòng {payment.room.room_name} đã thất bại",
                notification_type=NotificationType.PAYMENT,
                related_object_id=payment.id
            )
            # Thông báo cho chủ nhà
            Notifications.objects.create(
                receiver=payment.room.motel.user,
                title="Thanh toán thất bại",
                content=f"Thanh toán cho phòng {payment.room.room_name} từ {payment.payer.username} đã thất bại",
                notification_type=NotificationType.PAYMENT,
                related_object_id=payment.id
            )

        serializer = self.get_serializer(payment)
        return Response(serializer.data)

    # # Thống kê thanh toán
    # @action(detail=False, methods=['get'], url_path='statistics')
    # def payment_statistics(self, request):
    #     # Thống kê theo trạng thái
    #     status_stats = self.get_queryset().values('status').annotate(
    #         count=models.Count('id'),
    #         total_amount=models.Sum('amount')
    #     )

    #     # Thống kê theo phương thức thanh toán
    #     method_stats = self.get_queryset().values('payment_method').annotate(
    #         count=models.Count('id'),
    #         total_amount=models.Sum('amount')
    #     )

    #     # Tổng số thanh toán và tổng tiền
    #     total_stats = self.get_queryset().aggregate(
    #         total_count=models.Count('id'),
    #         total_amount=models.Sum('amount')
    #     )

    #     return Response({
    #         'status_stats': status_stats,
    #         'method_stats': method_stats,
    #         'total_stats': total_stats
    #     })
