from accommodationSearch import paginators, serializers
from django.contrib.auth import authenticate
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from rest_framework import generics, parsers, permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from unidecode import unidecode

from .models import (Admin, Comment, Follow, Landlord, LikeComment, Motel,
                     Notifications, Post, Room, Tenant, User)
from .permissions import IsOwnerOrReadOnly


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
    arser_classes = [parsers.MultiPartParser, ]

    def get_permissions(self):
        if self.action in ['create', 'login']:
            return [permissions.AllowAny()]
        return [permissions.IsAuthenticated()]

    def create(self, request, *args, **kwargs):
        role = request.data.get('role')
        if role == "LANDLORD":
            landlord_serializer = serializers.LandlordSerializer(data=request.data)
            if landlord_serializer.is_valid():
                landlord_serializer.save()
            else:
                return Response(landlord_serializer.errors, status=400)
        elif role == "TENANT":
            tenant_serializer = serializers.TenantSerializer(data=request.data)
            if tenant_serializer.is_valid():
                tenant_serializer.save()
            else:
                return Response(tenant_serializer.errors, status=400)
        else:
            return Response({"error": "Invalid role"}, status=400)

        return super().create(request, *args, **kwargs)

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

    @action(methods=['POST'], url_path='login', detail=False, permission_classes=[permissions.AllowAny])
    def login(self, request):
        username = request.data.get("username")
        password = request.data.get("password")
        user = authenticate(username=username, password=password)

        if user is not None:
            if user.is_active:
                return Response(self.serializer_class(user).data)
            else:
                return Response({"error": "user is inactive"}, status=403)
        return Response({"error": "Thông tin đăng nhập không hợp lệ"}, status=401)

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

    def retrieve(self, request, pk=None):
        if pk.isdigit():
            motel = get_object_or_404(Motel, id=pk)
        else:
            motel = get_object_or_404(Motel, slug=pk)

        serializers = self.get_serializer(motel)
        return Response(serializers.data)


class RoomViewSet(viewsets.ViewSet, generics.ListCreateAPIView, generics.RetrieveUpdateDestroyAPIView):
    queryset = Room.objects.filter(active=True)
    serializer_class = serializers.RoomSerializer
    pagination_class = paginators.ItemPanigator

    def retrieve(self, request, pk=None):
        if pk.isdigit():
            room = get_object_or_404(Room, id=pk)
        else:
            room = get_object_or_404(Room, slug=pk)

        serializers = self.get_serializer(room)
        return Response(serializers.data)

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


class LandlordViewSet(viewsets.ViewSet, generics.ListAPIView):
    queryset = Landlord.objects.filter(active=True)
    serializer_class = serializers.LandlordSerializer
    pagination_class = paginators.ItemPanigator

    def retrieve(self, request, pk=None):
        if pk.isdigit():
            landlord = get_object_or_404(Landlord, user_id=pk)
        else:
            landlord = get_object_or_404(Landlord, slug=pk)

        serializers = self.get_serializer(landlord)
        return Response(serializers.data)

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


class TenantViewSet(viewsets.ViewSet, generics.ListAPIView):
    queryset = Tenant.objects.filter(active=True)
    serializer_class = serializers.TenantSerializer
    pagination_class = paginators.ItemPanigator

    def retrieve(self, request, pk=None):
        if pk.isdigit():
            tenant = get_object_or_404(Tenant, user_id=pk)
        else:
            tenant = get_object_or_404(Tenant, slug=pk)

        serializers = self.get_serializer(tenant)
        return Response(serializers.data)

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
                    content=f"{self.request.user.username} has posted a new property: {post.title}",
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
        serializer.save()
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

    # Phương thức này thực hiện thao tác like (thích) cho một bình luận.
    @action(methods=['POST'], detail=True, url_path='like')
    def like_comment(self, request, pk):
        comment = self.get_object()
        like, created = LikeComment.objects.get_or_create(user=request.user, comment=comment)
        if not created:
            like.active = not like.active
        like.save()
        return Response(serializers.CommentSerializer(comment, context={'request': request}).data)

    # Phương thức này cho phép người dùng trả lời một bình luận.
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
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)
