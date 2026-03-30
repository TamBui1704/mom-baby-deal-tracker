FROM python:3.11-slim

# Cài đặt các gói hệ thống cần thiết (cho psycopg2)
RUN apt-get update && apt-get install -y \
    libpq-dev \
    gcc \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy requirements và cài đặt
COPY requirement.txt .
RUN pip install --no-cache-dir -r requirement.txt

# Copy mã nguồn
COPY . .

# Mặc định chạy consumer (sẽ bị docker-compose command override nếu cần)
CMD ["python", "src/consumers/main_consumer.py"]
