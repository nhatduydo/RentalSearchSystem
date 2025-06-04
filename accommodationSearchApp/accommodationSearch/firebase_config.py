import os

import firebase_admin
from django.conf import settings
from firebase_admin import credentials, db

FIREBASE_CREDENTIALS_PATH = os.getenv('FIREBASE_CREDENTIALS_PATH',
                                      os.path.join(settings.BASE_DIR, 'systemaccommodation-eca81-firebase-adminsdk-fbsvc-3a81cc66db.json'))

# Khởi tạo credentials từ file JSON chứa thông tin xác thực Firebase
cred = credentials.Certificate(FIREBASE_CREDENTIALS_PATH)

# Khởi tạo ứng dụng Firebase Admin với credentials và URL của database
firebase_admin.initialize_app(cred, {
    'databaseURL': 'https://systemaccommodation-eca81-default-rtdb.asia-southeast1.firebasedatabase.app/'
})

# Tạo reference đến node 'notifications' trong Realtime Database
notifications_ref = db.reference('notifications')


def send_notification(user_id, notification_data):
    """
    Gửi thông báo đến một user cụ thể

    Args:
        user_id: ID của người dùng cần gửi thông báo
        notification_data: Dữ liệu thông báo cần gửi (dạng dictionary)

    Flow:
    1. Tạo reference đến node notifications của user cụ thể
    2. Thêm thông báo mới vào node đó bằng phương thức push()
    """
    # Tạo reference đến node notifications của user cụ thể bằng cách thêm user_id vào path
    user_notifications_ref = notifications_ref.child(str(user_id))
    # Thêm thông báo mới vào node của user đó
    # Phương thức push() sẽ tự động tạo một key ngẫu nhiên cho thông báo
    user_notifications_ref.push(notification_data)
