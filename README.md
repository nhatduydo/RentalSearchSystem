# System_For_Searching_Accommodations
HỆ THỐNG HỖ TRỢ TÌM KIẾM NHÀ TRỌ
# 🌟 Dự Án Quản Lý Nhà Trọ 🌟

## 📋 Đăng Ký Tài Khoản
- **Chủ Trọ hoặc Người Thuê Trọ** (bắt buộc phải có avatar)

## 🔑 Đăng Nhập
- **Quản Trị Viên, Chủ Nhà Trọ, Người Thuê Trọ**

---

## 🛠️ Chức Năng Quản Trị Viên
- ✅ Quản lý người dùng (duyệt, khóa, xóa tài khoản)
- ✅ Duyệt tin đăng của chủ trọ (kiểm duyệt nội dung và hình ảnh)
- ✅ Quản lý báo cáo vi phạm
- 📊 Thống kê hệ thống
- 💳 Quản lý thanh toán
- ✅ Quản lý chứng thực nhà trọ
- 📢 Gửi thông báo hệ thống
- 🛠️ Quản lý danh mục tiện ích

---

## 🏠 Chức Năng Chủ Nhà Trọ
- 📝 Đăng ký tài khoản (bắt buộc cung cấp avatar, số điện thoại, hình ảnh trọ)
- 🛠️ Quản lý tin đăng
- 🗺️ Tích hợp Google Maps
- 💬 Trả lời bình luận của người thuê
- 🔔 Nhận thông báo khi có bình luận hoặc tin nhắn
- 👥 Quản lý danh sách người theo dõi
- 📣 Gửi thông báo cho người theo dõi
- ✅ Chứng thực nhà trọ
- 💰 Quản lý thanh toán và đặt cọc
- 📈 Xem thống kê tin đăng
- 🤖 Tích hợp chatbot hỗ trợ
- 💡 Tích hợp AI gợi ý giá thuê hợp lý

---

## 🏡 Chức Năng Người Thuê Trọ
- 📝 Đăng ký tài khoản (bắt buộc có avatar)
- 🔍 Tìm kiếm nhà trọ theo tiêu chí linh hoạt
- ❤️ Lưu tin yêu thích
- 💬 Bình luận & trao đổi với chủ trọ
- 👥 Theo dõi chủ trọ
- 📝 Đăng tin tìm phòng trọ
- 🔔 Nhận thông báo khi có chủ trọ phù hợp
- ⭐ Tích hợp đánh giá và phản hồi
- 💬 Tích hợp chat thời gian thực
- 🚨 Gửi báo cáo vi phạm
- 💡 Đề xuất giá thuê hợp lý

---

## 📊 Chức Năng Chung
- 🔒 Hệ thống đăng nhập & đăng ký bảo mật
- 💬 Tích hợp Firebase để chat thời gian thực
- 💳 Tích hợp thanh toán online
- 🔔 Thông báo đẩy
- 🔍 Bộ lọc tìm kiếm nâng cao
- ✅ Chứng thực thông tin chủ trọ
- 🗺️ Tích hợp bản đồ Google Maps
- 📈 Thống kê dữ liệu trên dashboard
- 🤖 Tích hợp AI hỗ trợ tìm trọ thông minh
- 💬 Tích hợp chatbot hỗ trợ tự động

---

## 🚀 Chức Năng Mở Rộng
- ⭐ Hệ thống đánh giá & phản hồi tin đăng
- 📜 Lịch sử giao dịch & thuê trọ
- 💳 Đặt cọc online ngay trên ứng dụng
- 📌 Chế độ hiển thị tin đăng nổi bật
- 🤖 Hệ thống gợi ý nhà trọ bằng AI
- 💬 Hỗ trợ chatbot AI
- 🌐 Hỗ trợ đa ngôn ngữ
- 📅 Tích hợp lịch hẹn xem phòng
- 📄 Hệ thống quản lý hợp đồng thuê trọ online

---

## 💻 Công Nghệ Đề Xuất
- **Backend**: Python Django + Django REST Framework (API)
- **Frontend Mobile**: React Native (Expo)
- **Database**: PostgreSQL / Firebase Firestore
- **Authentication**: JWT + OAuth
- **Real-time Chat**: Firebase
- **Maps & Location**: Google Maps API
- **Push Notification**: Firebase Cloud Messaging
- **Payment Gateway**: VNPay, ZaloPay, Stripe
- **Data Visualization**: Chart.js / Google Charts
- **AI Recommendation System**: TensorFlow / OpenAI API

---

## 📚 Mô Hình Class
```plaintext
User   & Roles
User   (username (PK), password, fullName, role , email, phone, avatar, address, createdDate)
Enum: UserRole (ADMIN, LANDLORD, TENANT)
Admin (username (PK, FK → User))
Landlord (username (PK, FK → User), landlordName, citizenId, bankAccount, isVerified (boolean)) 
Tenant (username (PK, FK → User), tenantName, citizenId, dateOfBirth, gender, bankAccount) 
Enum: Gender (MALE, FEMALE, OTHER)
Motel & Room System
Motel (id (PK), username (FK → User), motelName, description, address, latitude, longitude, totalRooms, availableRooms, status (boolean), ratingScore) 
Room (id (PK), motelId (FK), roomName, description, area, price, maxPeople, amenities, status (boolean))
MotelImage (id (PK), motelId (FK), imageUrl, imageType)
Enum: ImageType (INSIDE, OUTSIDE) 
RoomImage (id (PK), roomId (FK), imageUrl)
Posts & Comments
Post (id (PK), username (FK → User), postType, title, content, createdDate,
desiredAddress, minPrice, maxPrice, status (boolean)
+  desiredLatitude, desiredLongitude, // for FIND_ROOM
+ motelId (FK), // for RENT_OUT
)
Enum: PostType (RENT_OUT, FIND_ROOM)
Comment (id (PK), postId (FK), username (FK), content, createdDate)
MotelRating (id (PK), username (FK), motelId (FK), rating, comment, createdDate)
Social Features (Follow & Notifications)
Follow (id (PK), follower(FK → theo dõi), followed(FK → được theo dõi ), createdDate)
Notification (id (PK), receiverId (FK → User), title, content, isRead (boolean), createdDate, notificationType, relatedObjectId)
Enum: NotificationType (NEW_POST, NEW_COMMENT, COMMENT_REPLY, ACCOUNT_VERIFICATION, MOTEL_UPDATE, PAYMENT, SYSTEM)
Messaging System
ChatRoom (id (PK), user1Id (FK → User), user2Id (FK → User), lastMessageTime)
RealTimeChat (id (PK), senderId (FK → User), receiverId (FK → User), chatRoomId (FK → ChatRoom), content, timestamp, isRead (boolean))
Payment System
Payment (id (PK), payerId (FK → User), amount, paymentMethod, paymentStatus, roomId (FK → Room), paymentDate, description)
Enum: PaymentStatus (PENDING, COMPLETED, FAILED)
Enum: PaymentMethod (VNPAY, STRIPE, CASH)
Room Renting & Favorites
Room_Tenant (id (PK), roomId (FK → Room), tenantId (FK → Tenant), startDate, endDate, status, isPaid (boolean))
Enum status (ACTIVE, EXPIRED, CANCELLED, PENDING)
Favorite (id (PK), tenantId (FK → Tenant), roomId (FK → Room), createdDate)
