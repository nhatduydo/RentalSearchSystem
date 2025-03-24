# System_For_Searching_Accommodations
HỆ THỐNG HỖ TRỢ TÌM KIẾM NHÀ TRỌ
<!DOCTYPE html>
<html lang="vi">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Đăng ký và Quản lý Nhà Trọ</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            line-height: 1.6;
            margin: 20px;
            background-color: #f4f4f4;
            color: #333;
        }
        h1, h2, h3 {
            color: #2c3e50;
            text-align: center;
            margin-bottom: 20px;
        }
        p {
            margin: 15px 0;
            text-align: justify;
        }
        ul, ol {
            margin: 10px 0 20px 20px;
            padding-left: 20px;
        }
        li {
            margin-bottom: 10px;
        }
        table {
            width: 100%;
            border-collapse: collapse;
            margin: 20px 0;
        }
        th, td {
            border: 1px solid #ddd;
            padding: 8px;
            text-align: left;
        }
        th {
            background-color: #3498db;
            color: white;
        }
        a {
            color: #3498db;
            text-decoration: none;
        }
        a:hover {
            text-decoration: underline;
        }
        img {
            max-width: 100%;
            height: auto;
            display: block;
            margin: 0 auto;
        }
        button {
            background-color: #3498db;
            color: white;
            border: none;
            padding: 10px 20px;
            cursor: pointer;
            transition: background-color 0.3s;
        }
        button:hover {
            background-color: #2980b9;
        }
        .function-section {
            background-color: #ffffff;
            border: 1px solid #ddd;
            border-radius: 5px;
            padding: 15px;
            margin-bottom: 20px;
        }
        .function-section h3 {
            color: #2980b9;
        }
    </style>
</head>
<body>

    <h1>Đăng ký và Quản lý Nhà Trọ</h1>

    <h2>Đăng ký tài khoản</h2>
    <p>Chủ trọ hoặc người thuê trọ (bắt buộc phải có avatar)</p>
    <p>Đăng nhập (quản trị viên, chủ nhà trọ, người thuê trọ)</p>

    <div class="function-section">
        <h3>Quản trị viên</h3>
        <ul>
            <li>Đăng ký phải có avatar</li>
            <li>Xét duyệt cung cấp tối thiểu 3 hình ảnh:
                <ul>
                    <li>Dãy trọ, phòng trọ và có địa chỉ, số điện thoại liên hệ</li>
                    <li>Liên kết Google Map</li>
                </ul>
            </li>
            <li>Liên kết Google Map lưu thêm thông tin kinh độ và vĩ độ của điểm trọ.</li>
            <li>Đăng nhập thông kê số lượng người dùng, chủ trọ theo khoảng thời gian, tháng, năm, quý. (chartjs, googlejs) vẽ biểu đồ</li>
        </ul>
    </div>

    <div class="function-section">
        <h3>Chủ nhà trọ</h3>
        <ul>
            <li>Đăng tin:
                <ul>
                    <li>Ảnh minh họa trọ</li>
                    <li>Bình luận và trao đổi</li>
                </ul>
            </li>
            <li>Dùng Firebase tích hợp chat thời gian thực giữa các thành viên của mạng xã hội</li>
            <li>Bình luận và trao đổi với người thuê</li>
            <li>Đăng tin tìm trên hệ thống:
                <ul>
                    <li>Cung cấp phạm vi địa chỉ muốn thuê</li>
                    <li>Bình luận và trao đổi</li>
                </ul>
            </li>
            <li>Đề xuất cơ chế chứng thực thông tin nhà trò để đánh giá tính tin cậy được chủ trọ cung cấp</li>
            <li>Follow theo chủ nhà trọ, chủ nhà trọ đăng thông tin mới thì người theo dõi sẽ nhận thông báo qua email </li>
            <li>Nghiên cứu sử dụng Google Map để hiện thị và tương tác thông tin trọ trực tiếp trên bảng đồ.</li>
        </ul>
    </div>

    <div class="function-section">
        <h3>Người thuê trọ</h3>
        <ul>
            <li>Tìm trọ:
                <ul>
                    <li>Xung quanh một địa chỉ chỉ định</li>
                    <li>Theo quận/huyện/thành phố</li>
                    <li>Theo tiêu chí số lượng người ở</li>
                    <li>Theo mức giá mong muốn</li>
                </ul>
            </li>
            <li>Tương tác nhiều với cloud: chat, map, push notification</li>
            <li>Tích hợp thanh toán qua VNPay, ZaloPay, Stripe, …</li>
            <li>Cảm xúc qua văn bản, hình ảnh, emoji icon: các bình luận của người thuê về trọ => đánh giá tính tin cậy</li>
        </ul>
    </div>

    <h2>Chức năng</h2>
    <div class="function-section">
        <h3>Chức năng Quản trị viên</h3>
        <ul>
            <li>Quản lý người dùng (duyệt, khóa, xóa tài khoản)</li>
            <li>Duyệt tin đăng của chủ trọ (kiểm duyệt nội dung và hình ảnh)</li>
            <li>Quản lý báo cáo vi phạm (người dùng có thể báo cáo tin đăng sai sự thật)</li>
            <li>Thống kê hệ thống (số lượng tài khoản đăng ký, tin đăng, giao dịch thanh toán)</li>
            <li>Quản lý thanh toán (theo dõi và xử lý các giao dịch từ VNPay, ZaloPay, Stripe)</li>
            <li>Quản lý chứng thực nhà trọ (xác minh danh tính chủ trọ, hình ảnh trọ)</li>
            <li>Gửi thông báo hệ thống (push notification đến người dùng về cập nhật quan trọng)</li>
            <li>Quản lý danh mục tiện ích (ví dụ: điện nước, wifi, máy lạnh...)</li>
        </ul>
    </div>

    <div class="function-section">
        <h3>Chức năng Chủ nhà trọ</h3>
        <ul>
            <li>Đăng ký tài khoản (bắt buộc cung cấp avatar, số điện thoại, hình ảnh trọ)</li>
            <li>Quản lý tin đăng (thêm/sửa/xóa, cập nhật trạng thái phòng trọ)</li>
            <li>Tích hợp Google Maps (chọn vị trí phòng trọ trên bản đồ)</li>
            <li>Trả lời bình luận của người thuê</li>
            <li>Nhận thông báo khi có bình luận hoặc tin nhắn</li>
            <li>Quản lý danh sách người theo dõi (xem ai đang theo dõi tin đăng của mình)</li>
            <li>Gửi thông báo cho người theo dõi (về tin đăng mới)</li>
            <li>Chứng thực nhà trọ (nâng cao độ tin cậy bằng cách gửi giấy tờ xác minh)</li>
            <li>Quản lý thanh toán và đặt cọc (tích hợp VNPay, ZaloPay, Stripe)</li>
            <li>Xem thống kê tin đăng (lượt xem, lượt yêu thích, số người quan tâm)</li>
            <li>Tích hợp chatbot hỗ trợ (hỗ trợ phản hồi nhanh cho khách thuê)</li>
            <li>Tích hợp AI gợi ý giá thuê hợp lý (dựa trên khu vực và các thông tin liên quan)</li>
        </ul>
    </div>

    <div class="function-section">
        <h3>Chức năng Người thuê trọ</h3>
        <ul>
            <li>Đăng ký tài khoản (bắt buộc có avatar)</li>
            <li>Tìm kiếm nhà trọ theo tiêu chí linh hoạt:
                <ul>
                    <li>Theo vị trí (quận/huyện/thành phố, bản đồ Google Maps)</li>
                    <li>Theo giá tiền</li>
                    <li>Theo diện tích</li>
                    <li>Theo tiện ích (wifi, máy lạnh, chỗ để xe...)</li>
                    <li>Theo số lượng người ở</li>
                </ul>
            </li>
            <li>Lưu tin yêu thích</li>
            <li>Bình luận & trao đổi với chủ trọ</li>
            <li>Theo dõi chủ trọ (nhận thông báo khi có tin mới)</li>
            <li>Đăng tin tìm phòng trọ (cung cấp phạm vi địa điểm, yêu cầu, mô tả)</li>
            <li>Nhận thông báo khi có chủ trọ phù hợp bình luận trên tin tìm trọ</li>
            <li>Tích hợp đánh giá và phản hồi (cảm xúc qua văn bản, hình ảnh, emoji)</li>
            <li>Tích hợp chat thời gian thực bằng Firebase</li>
            <li>Gửi báo cáo vi phạm (nếu tin đăng sai sự thật)</li>
            <li>Đề xuất giá thuê hợp lý (dựa trên lịch sử thuê và gợi ý AI)</li>
        </ul>
    </div>

    <div class="function-section">
        <h3>Chức năng Chung</h3>
        <ul>
            <li>Hệ thống đăng nhập & đăng ký bảo mật (JWT Token, Google/Facebook Login)</li>
            <li>Tích hợp Firebase để chat thời gian thực</li>
            <li>Tích hợp thanh toán online (VNPay, ZaloPay, Stripe cho cọc hoặc tiền thuê)</li>
            <li>Thông báo đẩy (Push Notification)</li>
            <li>Bộ lọc tìm kiếm nâng cao (lọc theo giá, tiện ích, vị trí...)</li>
            <li>Chứng thực thông tin chủ trọ (duyệt giấy tờ, xác minh danh tính)</li>
            <li>Tích hợp bản đồ Google Maps (hiển thị nhà trọ trực tiếp trên bản đồ)</li>
            <li>Thống kê dữ liệu trên dashboard (Chart.js, Google Charts)</li>
            <li>Tích hợp AI hỗ trợ tìm trọ thông minh (gợi ý theo sở thích, thói quen)</li>
            <li>Tích hợp chatbot hỗ trợ tự động (trả lời câu hỏi cơ bản)</li>
        </ul>
    </div>

    <div class="function-section">
        <h3>Chức năng Mở rộng (Gợi ý nâng cao)</h3>
        <ul>
            <li>Hệ thống đánh giá & phản hồi tin đăng (người thuê đánh giá mức độ hài lòng với trọ)</li>
            <li>Lịch sử giao dịch & thuê trọ (xem lại các trọ đã từng thuê)</li>
            <li>Đặt cọc online ngay trên ứng dụng (giúp đảm bảo tính an toàn)</li>
            <li>Chế độ hiển thị tin đăng nổi bật (trả phí để hiển thị tin lên đầu)</li>
            <li>Hệ thống gợi ý nhà trọ bằng AI (học từ lịch sử tìm kiếm của người dùng)</li>
            <li>Hỗ trợ chatbot AI (tư vấn giá trọ, khu vực phù hợp)</li>
            <li>Hỗ trợ đa ngôn ngữ (tiếng Anh, tiếng Việt...)</li>
            <li>Tích hợp lịch hẹn xem phòng (đặt lịch hẹn với chủ trọ trực tiếp trong app)</li>
            <li>Hệ thống quản lý hợp đồng thuê trọ online (tạo hợp đồng, ký điện tử)</li>
        </ul>
    </div>

    <h2>Công nghệ Đề Xuất</h2>
    <ul>
        <li>Backend: Python Django + Django REST Framework (API)</li>
        <li>Frontend Mobile: React Native (Expo)</li>
        <li>Database: PostgreSQL / Firebase Firestore (chat)</li>
        <li>Authentication: JWT + OAuth (Google, Facebook Login)</li>
        <li>Real-time Chat: Firebase</li>
        <li>Maps & Location: Google Maps API</li>
        <li>Push Notification: Firebase Cloud Messaging (FCM)</li>
        <li>Payment Gateway: VNPay, ZaloPay, Stripe</li>
        <li>Data Visualization: Chart.js / Google Charts</li>
        <li>AI Recommendation System: TensorFlow / OpenAI API</li>
    </ul>

    <h2>Mô hình class</h2>
    <pre>
User  & Roles
User  (username (PK), password, fullName, role , email, phone, avatar, address, createdDate)
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
+ desiredLatitude, desiredLongitude, // for FIND_ROOM
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
    </pre>
</body>
</html>
