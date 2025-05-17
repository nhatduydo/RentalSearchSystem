import json

import mysql.connector

# Cấu hình kết nối
config = {
    'host': 'localhost',
    'user': 'root',
    'password': 'Admin@123',
    'database': 'rentalmanagementdb',
}

conn = mysql.connector.connect(**config)
cursor = conn.cursor()

# Lấy danh sách tất cả các bảng
cursor.execute("SHOW TABLES")
tables = [row[0] for row in cursor.fetchall()]

database_json = {}

for table in tables:
    # Lấy thông tin về các cột và kiểu dữ liệu của chúng
    cursor.execute(f"SHOW COLUMNS FROM {table}")
    columns_info = cursor.fetchall()

    # Lấy dữ liệu từ bảng
    cursor.execute(f"SELECT * FROM {table}")
    columns = [desc[0] for desc in cursor.description]
    rows = cursor.fetchall()

    # Xử lý dữ liệu và loại bỏ auto-increment
    records = []
    for row in rows:
        record = {}
        for i, col in enumerate(columns):
            # Kiểm tra xem cột có phải là auto-increment không
            is_auto_increment = any(col_info[0] == col and 'auto_increment' in col_info[5].lower()
                                    for col_info in columns_info)

            # Nếu là auto-increment, vẫn giữ giá trị id
            if is_auto_increment:
                record[col] = row[i]
            else:
                record[col] = row[i]
        records.append(record)

    database_json[table] = records

# Lưu ra file JSON, dùng default=str để chuyển đổi datetime
with open("full_database.json", "w", encoding="utf-8") as f:
    json.dump(database_json, f, indent=4, ensure_ascii=False, default=str)

cursor.close()
conn.close()

print("✅ Export toàn bộ database thành công: full_database.json")
