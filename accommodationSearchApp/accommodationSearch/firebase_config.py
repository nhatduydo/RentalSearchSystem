import os

import firebase_admin
from django.conf import settings
from firebase_admin import credentials, db

FIREBASE_CREDENTIALS_PATH = os.getenv('FIREBASE_CREDENTIALS_PATH',
                                      os.path.join(settings.BASE_DIR, 'systemaccommodation-eca81-firebase-adminsdk-fbsvc-3a81cc66db.json'))

cred = credentials.Certificate(FIREBASE_CREDENTIALS_PATH)
firebase_admin.initialize_app(cred, {
    'databaseURL': 'https://systemaccommodation-eca81-default-rtdb.asia-southeast1.firebasedatabase.app/'
})

notifications_ref = db.reference('notifications')


def send_notification(user_id, notification_data):
    """
    Gửi thông báo đến một user cụ thể
    """
    user_notifications_ref = notifications_ref.child(str(user_id))
    user_notifications_ref.push(notification_data)
