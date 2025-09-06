FROM python:3.10-slim

# Cài dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    default-libmysqlclient-dev \
    && rm -rf /var/lib/apt/lists/*

# Tạo thư mục app
WORKDIR /app

# Copy requirements.txt vào container
COPY accommodationSearchApp/accommodationSearchApp/requirements.txt .

# Cài dependencies Python
RUN pip install --no-cache-dir -r requirements.txt

# Copy toàn bộ code
COPY . .

# Collect static files
RUN python accommodationSearchApp/accommodationSearchApp/manage.py collectstatic --noinput

# Expose cổng 8000
EXPOSE 8000

# Chạy bằng Gunicorn
CMD ["gunicorn", "accommodationSearchApp.wsgi:application", "--bind", "0.0.0.0:8000"]
