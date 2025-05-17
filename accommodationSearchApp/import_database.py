import json
import os

import mysql.connector

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
    'accommodationsearch_user',
    'accommodationsearch_user_groups',
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
    'accommodationsearch_amenity',
    'accommodationsearch_landlord',
    'accommodationsearch_tenant',
    'accommodationsearch_motel',
    'accommodationsearch_room',
    'accommodationsearch_room_amenities',
    'accommodationsearch_motelimage',
    'accommodationsearch_roomimage',
    'accommodationsearch_roomtenant',
    'accommodationsearch_motelrating',
    'accommodationsearch_post',
    'accommodationsearch_comment',
    'accommodationsearch_likecomment',
    'accommodationsearch_likemotel',
    'accommodationsearch_searchhistory',
    'accommodationsearch_follow',
    'accommodationsearch_notifications',
    'accommodationsearch_chatroom',
    'accommodationsearch_chatroom_participants',
    'accommodationsearch_message',
    'accommodationsearch_payment'
]


# def create_tables(cursor):
#     """Tạo các bảng nếu chưa tồn tại"""
#     # Đọc file SQL để tạo bảng
#     sql_file = os.path.join(os.path.dirname(__file__), 'create_tables.sql')
#     if os.path.exists(sql_file):
#         with open(sql_file, 'r', encoding='utf-8') as f:
#             sql_commands = f.read().split(';')
#             for command in sql_commands:
#                 if command.strip():
#                     try:
#                         cursor.execute(command)
#                     except mysql.connector.Error as err:
#                         print(f"⚠️ Lỗi khi tạo bảng: {err}")
#     else:
#         print("⚠️ Không tìm thấy file create_tables.sql")


def import_data():
    try:
        conn = mysql.connector.connect(**config)
        cursor = conn.cursor()

        # Tắt kiểm tra khóa ngoại
        cursor.execute("SET FOREIGN_KEY_CHECKS = 0")
        conn.commit()

        # Đọc dữ liệu từ file JSON
        with open("full_database.json", "r", encoding="utf-8") as f:
            database_json = json.load(f)

        # Import dữ liệu theo thứ tự
        for table in IMPORT_ORDER:
            if table in database_json:
                try:
                    # Xóa dữ liệu cũ
                    cursor.execute(f"DELETE FROM {table}")

                    # Lấy dữ liệu mới
                    records = database_json[table]
                    if records:
                        # Lấy tên các cột
                        columns = records[0].keys()
                        # Tạo câu lệnh INSERT với tên cột trong backtick
                        placeholders = ', '.join(['%s'] * len(columns))
                        columns_str = ', '.join([f'`{col}`' for col in columns])
                        insert_query = f"INSERT INTO {table} ({columns_str}) VALUES ({placeholders})"

                        # Thực hiện insert
                        values = [[record[col] for col in columns] for record in records]
                        cursor.executemany(insert_query, values)
                        conn.commit()

                        print(f"✔️ Đã import bảng {table} ({len(records)} dòng)")
                    else:
                        print(f"ℹ️ Bảng {table} không có dữ liệu")
                except mysql.connector.Error as err:
                    print(f"❌ Lỗi import bảng {table}: {err}")
                    conn.rollback()

                    # Xử lý các lỗi đặc biệt
                    if "syntax" in str(err).lower():
                        print(f"⚠️ Lỗi cú pháp SQL: Kiểm tra lại cấu trúc dữ liệu của bảng {table}")
                        # In ra dữ liệu gây lỗi để debug
                        print(f"📝 Dữ liệu mẫu từ bảng {table}:")
                        print(json.dumps(records[0], indent=2, ensure_ascii=False))
                    elif "doesn't exist" in str(err):
                        print(f"⚠️ Bảng {table} chưa được tạo. Kiểm tra lại cấu trúc database")

        # Bật lại kiểm tra khóa ngoại
        cursor.execute("SET FOREIGN_KEY_CHECKS = 1")
        conn.commit()

        print("✅ Import database hoàn tất!")

    except mysql.connector.Error as err:
        print(f"❌ Lỗi kết nối database: {err}")
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals():
            conn.close()


if __name__ == "__main__":
    import_data()
