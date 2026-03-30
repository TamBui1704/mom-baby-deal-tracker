FROM apache/airflow:2.7.1

# Chuyển sang quyền root để cài đặt các gói hệ thống nếu cần
USER root
RUN apt-get update && apt-get install -y \
    libpq-dev \
    gcc \
    curl \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

# Quay lại user airflow để cài đặt python packages
USER airflow
COPY requirement.txt /requirement.txt
RUN pip install --no-cache-dir -r /requirement.txt
