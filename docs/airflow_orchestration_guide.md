# Hướng dẫn Xây dựng Luồng Airflow & Kafka chuyên nghiệp

Tư duy dự án của bạn hiện tại rất chính xác và sát với thực tế tại các công ty dữ liệu lớn (như Grab, Shopee). Việc tách luồng **"Nóng" (Alert)** và **"Lạnh" (Storage)** giúp hệ thống vừa nhanh, vừa bền.

Dưới đây là cách triển khai chi tiết:

## 1. Kiến trúc Tổng thể (Hybrid Flow)

| Thành phần | Loại luồng | Công cụ quản lý | Nhiệm vụ |
| :--- | :--- | :--- | :--- |
| **Scraper** | Batch (15p/lần) | **Airflow** | Cào dữ liệu, đẩy vào Kafka topic `price_raw`. |
| **Consumer** | Stream (Liên tục) | **Docker (Restart: Always)** | Lắng nghe Kafka, thực hiện Việc A, B, C ngay lập tức. |
| **dbt Transform** | Batch (Định kỳ) | **Airflow** | Làm sạch/Tổng hợp dữ liệu trong DWH để phục vụ báo cáo. |

---

## 2. Triển khai Airflow DAG (Luồng Ingestion)

Bạn sẽ tạo một file DAG trong folder `orchestration/dags/price_ingestion.py`. Airflow sẽ đóng vai trò "người báo thức" gọi Scraper dậy làm việc.

```python
from airflow import DAG
from airflow.operators.bash import BashOperator
from datetime import datetime, timedelta

default_args = {
    'owner': 'tambui',
    'retry_delay': timedelta(minutes=5),
}

with DAG(
    'scraper_ingestion_flow',
    default_args=default_args,
    schedule_interval='*/15 * * * *', # Chạy mỗi 15 phút
    start_date=datetime(2026, 3, 1),
    catchup=False
) as dag:

    run_scraper = BashOperator(
        task_id='run_price_scraper',
        bash_command='python /app/src/producers/price_producer.py'
    )
    
    run_dbt = BashOperator(
        task_id='run_dbt_refresh',
        bash_command='cd /app/analytics/dbt && dbt run --profiles-dir .'
    )

    run_scraper >> run_dbt
```

---

## 3. Triển khai Consumer "Always-on" (Việc A, B, C)

Vì Consumer là luồng Stream (chạy mãi mãi), chúng ta **không** đưa nó vào Airflow Task (vì Airflow không sinh ra để quản lý các tiến trình chạy vĩnh viễn). Thay vào đó, ta quản lý nó bằng Docker.

Trong `docker-compose.yml`, bạn nên thêm service này:

```yaml
  stream-processor:
    build: .
    container_name: kafka_consumer_worker
    command: python src/consumers/main_consumer.py
    restart: always # Tự động bật lại nếu bị sập
    depends_on:
      - message-broker
      - warehouse-db
```

### Tại sao giải pháp này tối ưu?
1.  **Sự kiện là Trigger**: Ngay khi Scraper (do Airflow gọi) đẩy 1 message vào Kafka, Consumer (đang chạy sẵn) sẽ "tớp" được ngay. 
2.  **Độ trễ (Latency)**: Alert Telegram sẽ nổ sau chỉ khoảng 100-200ms kể từ khi dữ liệu vào Kafka.
3.  **Tính độc lập**: Nếu Airflow bị treo, Consumer vẫn đang chạy và xử lý dữ liệu tồn đọng trong Kafka. Nếu Consumer treo, Kafka sẽ giữ dữ liệu cho đến khi Consumer quay lại.

---

## 4. Lời khuyên cho "Product mindset"
Khi bạn làm Product, bạn sẽ quan tâm đến **"Time-to-Value"**.
*   **Alert (Nóng)**: Mang lại giá trị tức thời cho người dùng (mua được hàng rẻ).
*   **Dashboard (Lạnh)**: Giúp bạn đưa ra quyết định chiến lược (tháng sau nên bắt tay với Shopee hay Lazada).

Với luồng này, bạn đã có một hệ thống **Modern Data Stack** cực kỳ mạnh mẽ!
