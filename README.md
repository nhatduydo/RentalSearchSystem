(System_For_Searching_Accommodations)

Ứng dụng hỗ trợ tìm kiếm, đăng tin và quản lý nhà trọ, kết nối chủ nhà trọ – người thuê trọ – quản trị viên trên cùng một nền tảng.
Dự án được xây dựng với Django REST Framework (backend) và React Native (frontend mobile), tích hợp nhiều công nghệ hiện đại như Firebase realtime chat, Google Maps API, AI recommendation, online payment.

✨ Tính năng chính
👨‍💼 Quản trị viên (Admin)

Quản lý người dùng (duyệt, khóa, xóa tài khoản).

Kiểm duyệt tin đăng của chủ trọ (nội dung, hình ảnh).

Quản lý báo cáo vi phạm.

Thống kê hệ thống (theo ngày/tháng/năm).

Quản lý thanh toán & chứng thực nhà trọ.

Gửi thông báo hệ thống.

Quản lý danh mục tiện ích.

🏠 Chủ nhà trọ (Landlord)

Đăng ký tài khoản (yêu cầu avatar, số điện thoại, ít nhất 3 hình ảnh dãy/phòng trọ).

Quản lý tin đăng (thêm/sửa/xóa/báo cáo).

Tích hợp Google Maps (tọa độ, địa chỉ chính xác).

Trả lời bình luận của người thuê.

Nhận thông báo khi có bình luận/tin nhắn.

Quản lý danh sách người theo dõi, gửi thông báo cho followers.

Quản lý chứng thực nhà trọ.

Quản lý thanh toán và đặt cọc.

Xem thống kê tin đăng.

Hỗ trợ chatbot và AI gợi ý giá thuê hợp lý.

👤 Người thuê trọ (Tenant)

Đăng ký tài khoản (yêu cầu avatar).

Tìm kiếm nhà trọ theo tiêu chí linh hoạt: vị trí, giá, số người, khu vực.

Lưu tin yêu thích, bình luận và trao đổi với chủ trọ.

Theo dõi chủ nhà trọ, nhận thông báo khi có tin mới.

Đăng tin tìm phòng.

Gửi báo cáo vi phạm.

Đánh giá và phản hồi tin đăng.

Chat thời gian thực qua Firebase.

Nhận gợi ý giá thuê hợp lý từ AI.

📊 Chức năng chung

Đăng nhập/đăng ký bảo mật (JWT + OAuth).

Chat realtime (Firebase).

Tích hợp bản đồ Google Maps.

Thanh toán online (VNPay, ZaloPay, Stripe).

Thông báo đẩy (Firebase Cloud Messaging).

Bộ lọc tìm kiếm nâng cao.

Chứng thực thông tin chủ trọ.

Thống kê dữ liệu hiển thị qua Chart.js / Google Charts.

AI hỗ trợ tìm trọ thông minh & chatbot tự động.

🚀 Chức năng mở rộng

Hệ thống đánh giá & phản hồi tin đăng.

Lịch sử giao dịch & thuê trọ.

Đặt cọc online ngay trong ứng dụng.

Hiển thị tin nổi bật.

Hỗ trợ đa ngôn ngữ.

Tích hợp lịch hẹn xem phòng.

Quản lý hợp đồng thuê trọ online.

🏗️ Kiến trúc hệ thống

Backend: Python Django + Django REST Framework (API).

Frontend Mobile: React Native (Expo).

Database: PostgreSQL / Firebase Firestore.

Authentication: JWT + OAuth2.

Realtime Chat: Firebase Realtime Database.

Maps & Location: Google Maps API.

Notifications: Firebase Cloud Messaging.

Payment Gateway: VNPay, ZaloPay, Stripe.

Data Visualization: Chart.js / Google Charts.

AI Recommendation System: TensorFlow / OpenAI API.

⚙️ Hướng dẫn cài đặt
1️⃣ Clone project
```
git clone https://github.com/<your-username>/System_For_Searching_Accommodations.git
cd System_For_Searching_Accommodations
```
2️⃣ Cấu hình Backend (Django)
```
cd backend
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver
```
3️⃣ Cấu hình Frontend (React Native)
```
cd frontend
npm install
npm start
```
4️⃣ Cấu hình Database

Tạo database PostgreSQL hoặc Firebase Firestore.

Cập nhật thông tin DB trong file .env.

5️⃣ Tích hợp API

Google Maps API Key

Firebase Project (chat + notification)

VNPay/ZaloPay/Stripe credentials

📂 Cấu trúc dự án (rút gọn)
```
System_For_Searching_Accommodations/
 ├── backend/             # Django REST API
 │   ├── apps/            # Modules: users, rentals, payments, chat
 │   ├── settings.py      # Config + JWT + OAuth
 │   └── tests/           # Unit tests
 ├── frontend/            # React Native app
 │   ├── screens/         # Giao diện (Home, Search, Chat, Payment)
 │   ├── components/      # Reusable UI
 │   └── services/        # API connection
 └── docs/                # Tài liệu hướng dẫn

```
👥 Nhóm phát triển

Team size: 2 người.

Vai trò:

Backend: xây dựng API với Django, thiết kế DB, tích hợp Google Maps, thanh toán, AI gợi ý.

Frontend: xây dựng ứng dụng mobile bằng React Native, tích hợp Firebase chat, thông báo đẩy.

📌 Ghi chú

Đây là dự án học thuật nhưng có thể mở rộng thành ứng dụng thực tế.

Tương lai có thể bổ sung thêm: OCR xác thực giấy tờ thuê trọ, Machine Learning dự đoán giá thuê, Chatbot nâng cao.
