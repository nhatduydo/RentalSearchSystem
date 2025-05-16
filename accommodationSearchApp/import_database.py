import mysql.connector
import json

# Cấu hình kết nối tới DB mới
config = {
    'host': 'localhost',
    'user': 'root',
    'password': 'Admin@123',
    'database': 'rentalmanagementdb',
}

conn = mysql.connector.connect(**config)
cursor = conn.cursor()

# Đọc file JSON export
with open("full_database.json", "r", encoding="utf-8") as f:
    database_json = json.load(f)

for table, records in database_json.items():
    if not records:
        continue  # Bỏ qua bảng trống
    
    columns = records[0].keys()
    cols_str = ", ".join(f"`{col}`" for col in columns)
    placeholders = ", ".join(["%s"] * len(columns))

    insert_query = f"INSERT INTO `{table}` ({cols_str}) VALUES ({placeholders})"

    values = []
    for record in records:
        # Đảm bảo kiểu dữ liệu phù hợp nếu cần
        row = tuple(record[col] for col in columns)
        values.append(row)

    try:
        cursor.executemany(insert_query, values)
        conn.commit()
        print(f"✔️ Đã import bảng {table} ({len(records)} dòng)")
    except mysql.connector.Error as err:
        print(f"❌ Lỗi import bảng {table}: {err}")
        conn.rollback()

cursor.close()
conn.close()
print("✅ Import database hoàn tất!")
