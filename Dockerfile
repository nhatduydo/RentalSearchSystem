FROM python:3.10-slim

# Cài dependencies hệ thống cho mysqlclient
RUN apt-get update && apt-get install -y \
    build-essential \
    default-libmysqlclient-dev \
    pkg-config \
    && rm -rf /var/lib/apt/lists/*

# Thư mục làm việc
WORKDIR /app

# Copy requirements trước để cache
COPY accommodationSearchApp/requirements.txt .

# Cài Python packages
RUN pip install --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt \
    && pip install gunicorn

# Copy toàn bộ source code
COPY accommodationSearchApp/ .

# Collect static files
RUN python manage.py collectstatic --noinput || true

EXPOSE 8000

CMD ["gunicorn", "accommodationSearchApp.wsgi:application", "--bind", "0.0.0.0:8000"]
