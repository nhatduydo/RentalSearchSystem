import mysql.connector
import json

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
    cursor.execute(f"SELECT * FROM {table}")
    columns = [desc[0] for desc in cursor.description]
    rows = cursor.fetchall()
    records = [dict(zip(columns, row)) for row in rows]
    database_json[table] = records

# Lưu ra file JSON, dùng default=str để chuyển đổi datetime
with open("full_database.json", "w", encoding="utf-8") as f:
    json.dump(database_json, f, indent=4, ensure_ascii=False, default=str)

cursor.close()
conn.close()

print("✅ Export toàn bộ database thành công: full_database.json")
