import json
import os
import shutil
import sys

import django
import mysql.connector
from django.conf import settings
from django.core.management import call_command

# Thiết lập Django environment
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'accommodationSearchApp.settings')
django.setup()

# Cấu hình kết nối
config = {
    'host': '',
    'user': 'root',
    'password': 'Admin@123',
    'database': 'rentalmanagementdb',
}

# Thứ tự import các bảng (để tránh lỗi khóa ngoại)
IMPORT_ORDER = [
    # Django system tables - thứ tự cơ bản
    'django_site',
    'django_content_type',
    'django_migrations',
    'django_session',

    # Auth tables - thứ tự cơ bản
    'auth_permission',
    'auth_group',
    'auth_group_permissions',

    # User related tables - thứ tự cơ bản
    'accommodationSearch_user',
    'accommodationSearch_user_groups',
    'account_emailaddress',

    # Django admin log (sau khi có user)
    'django_admin_log',

    # OAuth related tables
    'oauth2_provider_application',
    'oauth2_provider_accesstoken',
    'oauth2_provider_refreshtoken',

    # Social account tables
    'socialaccount_socialapp',
    'socialaccount_socialapp_sites',
    'socialaccount_socialaccount',

    # Main application tables - thứ tự cơ bản
    'accommodationSearch_amenity',
    'accommodationSearch_landlord',
    'accommodationSearch_tenant',
    'accommodationSearch_motel',
    'accommodationSearch_room',
    'accommodationSearch_room_amenities',
    'accommodationSearch_motelimage',
    'accommodationSearch_roomimage',
    'accommodationSearch_roomtenant',
    'accommodationSearch_motelrating',
    'accommodationSearch_post',
    'accommodationSearch_comment',
    'accommodationSearch_likecomment',
    'accommodationSearch_likemotel',
    'accommodationSearch_searchhistory',
    'accommodationSearch_follow',
    'accommodationSearch_notifications',
    'accommodationSearch_chatroom',
    'accommodationSearch_chatroom_participants',
    'accommodationSearch_message',
    'accommodationSearch_payment'
]


def check_app_installed():
    """Kiểm tra xem app accommodationSearch đã được cài đặt chưa"""
    if 'accommodationSearch.apps.AccommodationsearchConfig' not in settings.INSTALLED_APPS:
        print("❌ App 'accommodationSearch' chưa được thêm vào INSTALLED_APPS trong settings.py")
        print("Vui lòng thêm 'accommodationSearch.apps.AccommodationsearchConfig' vào INSTALLED_APPS trong file settings.py")
        sys.exit(1)
    print("✅ App 'accommodationSearch' đã được cài đặt")


def clean_migrations():
    """Xóa tất cả migrations cũ"""
    print("\n🧹 Đang xóa migrations cũ...")
    migrations_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'accommodationSearch', 'migrations')

    # Xóa tất cả file migrations trừ __init__.py
    if os.path.exists(migrations_dir):
        for file in os.listdir(migrations_dir):
            if file != '__init__.py':
                file_path = os.path.join(migrations_dir, file)
                if os.path.isfile(file_path):
                    os.remove(file_path)
                    print(f"Đã xóa: {file}")
    print("✅ Đã xóa migrations cũ")


def setup_database():
    """Tạo và cập nhật database schema sử dụng Django migrations"""
    print("\n🔄 Đang tạo và cập nhật cấu trúc database...")
    try:
        # Kiểm tra app đã được cài đặt
        check_app_installed()

        # Xóa migrations cũ
        clean_migrations()

        # Tạo migrations mới
        print("\n📝 Đang tạo migrations mới...")
        call_command('makemigrations', 'accommodationSearch')

        # Áp dụng migrations
        print("\n📦 Đang áp dụng migrations...")
        call_command('migrate', 'accommodationSearch', 'zero')  # Reset migrations
        call_command('migrate')  # Apply all migrations

        # Kiểm tra các bảng đã được tạo
        conn = mysql.connector.connect(**config)
        cursor = conn.cursor()
        cursor.execute("SHOW TABLES")
        tables = cursor.fetchall()
        print("\n📊 Các bảng đã được tạo:")
        for table in tables:
            print(f"- {table[0]}")
        cursor.close()
        conn.close()

        print("\n✅ Đã tạo và cập nhật cấu trúc database thành công!")
    except Exception as e:
        print(f"❌ Lỗi khi tạo/cập nhật database: {str(e)}")
        raise


def get_table_mapping():
    """Tạo mapping giữa tên bảng trong JSON và tên bảng trong database"""
    conn = mysql.connector.connect(**config)
    cursor = conn.cursor()
    cursor.execute("SHOW TABLES")
    tables = [table[0] for table in cursor.fetchall()]
    cursor.close()
    conn.close()

    # Tạo mapping từ tên bảng viết thường sang tên bảng thực tế
    mapping = {}
    for table in tables:
        mapping[table.lower()] = table
    return mapping


def import_data():
    try:
        print("\n🚀 Bắt đầu quá trình import database...")

        # Tạo và cập nhật cấu trúc database trước
        setup_database()

        # Lấy mapping tên bảng
        table_mapping = get_table_mapping()

        conn = mysql.connector.connect(**config)
        cursor = conn.cursor()

        # Tắt kiểm tra khóa ngoại
        cursor.execute("SET FOREIGN_KEY_CHECKS = 0")
        conn.commit()

        # Đọc dữ liệu từ file JSON
        print("\n📖 Đang đọc dữ liệu từ file JSON...")
        with open("full_database.json", "r", encoding="utf-8") as f:
            database_json = json.load(f)

        # Import dữ liệu theo thứ tự
        print("\n📥 Đang import dữ liệu vào các bảng...")
        for table in IMPORT_ORDER:
            # Chuyển đổi tên bảng sang chữ thường để tìm trong JSON
            json_table = table.lower()
            if json_table in database_json:
                try:
                    # Lấy tên bảng thực tế từ mapping
                    actual_table = table_mapping.get(json_table)
                    if not actual_table:
                        print(f"⚠️ Không tìm thấy bảng {table} trong database")
                        continue

                    # Xóa dữ liệu cũ
                    cursor.execute(f"DELETE FROM {actual_table}")

                    # Lấy dữ liệu mới
                    records = database_json[json_table]
                    if records:
                        # Lấy tên các cột
                        columns = records[0].keys()
                        # Tạo câu lệnh INSERT với tên cột trong backtick
                        placeholders = ', '.join(['%s'] * len(columns))
                        columns_str = ', '.join([f'`{col}`' for col in columns])
                        insert_query = f"INSERT INTO {actual_table} ({columns_str}) VALUES ({placeholders})"

                        # Thực hiện insert
                        values = [[record[col] for col in columns] for record in records]
                        cursor.executemany(insert_query, values)
                        conn.commit()

                        print(f"✅ Đã import bảng {actual_table} ({len(records)} dòng)")
                    else:
                        print(f"ℹ️ Bảng {actual_table} không có dữ liệu")
                except mysql.connector.Error as err:
                    print(f"❌ Lỗi import bảng {actual_table}: {err}")
                    conn.rollback()

                    # Xử lý các lỗi đặc biệt
                    if "syntax" in str(err).lower():
                        print(f"⚠️ Lỗi cú pháp SQL: Kiểm tra lại cấu trúc dữ liệu của bảng {actual_table}")
                        # In ra dữ liệu gây lỗi để debug
                        print(f"📝 Dữ liệu mẫu từ bảng {actual_table}:")
                        print(json.dumps(records[0], indent=2, ensure_ascii=False))
                    elif "doesn't exist" in str(err):
                        print(f"⚠️ Bảng {actual_table} chưa được tạo. Kiểm tra lại cấu trúc database")

        # Bật lại kiểm tra khóa ngoại
        cursor.execute("SET FOREIGN_KEY_CHECKS = 1")
        conn.commit()

        print("\n🎉 Import database hoàn tất!")

    except mysql.connector.Error as err:
        print(f"\n❌ Lỗi kết nối database: {err}")
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals():
            conn.close()


if __name__ == "__main__":
    import_data()
