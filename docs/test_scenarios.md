# Kịch bản Kiểm thử Dự án Mom & Baby Pipeline

Tài liệu này hướng dẫn chi tiết cách kiểm tra toàn bộ luồng dữ liệu từ công đoạn cào dữ liệu đến khi dữ liệu vào Data Warehouse.

## 1. Kiểm tra Hạ tầng (Infrastructure)

### Bước 1: Khởi động hệ thống
```bash
docker compose up -d --build
```
*(Hệ thống sẽ tự động tạo topic `price_raw` thông qua container `kafka_init`)*

**Kỳ vọng:**

---

## 2. Kiểm tra Luồng Ingestion (Scraper -> Kafka)

### Bước 2: Chạy Scraper thủ công (Manual Test)
Mục đích: Kiểm tra khả năng gửi tin nhắn DATA và EOF Marker.
```bash
# Chạy từ host hoặc vào container worker
docker exec -it airflow_orchestrator bash
export KAFKA_BOOTSTRAP_SERVERS=message-broker:9092
export BATCH_ID=test_batch_001
# Trong container Airflow, dùng python3
python3 /app/src/producers/scrapers/price_producer.py

# Sau khi xong, gõ 'exit' hoặc nhấn Ctrl+D để thoát ra máy thật
exit
```


> [!TIP]
> **Lưu ý về Python**: 
> - Nếu bạn chạy **trong container** (như trên): Dùng lệnh `python3`.
> - Nếu bạn chạy **ngoài Host** (máy thật): Hãy nhớ kích hoạt môi trường ảo trước (`source venv/bin/activate` trên Linux/WSL hoặc `.\venv\Scripts\activate` trên Windows) và dùng lệnh `python`.

**Kỳ vọng:**
- [ ] Log hiển thị: `Sent 3 data messages + 1 EOF marker`.
- [ ] Dùng lệnh CLI để kiểm tra 4 tin nhắn mới trong Kafka:
  ```bash
  docker exec -it kafka_broker kafka-console-consumer.sh --bootstrap-server localhost:9092 --topic price_raw --from-beginning --max-messages 4
  ```

---

## 3. Kiểm tra Luồng Xử lý (Consumer -> Data Lake & Alert)

### Bước 3: Kiểm tra Data Lake (Postgres)
```sql
-- Kết nối vào warehouse-db (mom_baby_dw)
SELECT * FROM raw.stg_price_events WHERE batch_id = 'test_batch_001';
```
**Kỳ vọng:**
- [ ] Có đầy đủ bản ghi dữ liệu sản phẩm.
- [ ] Cột `raw_data` chứa JSON nguyên bản.
- [ ] Cột `batch_id` khớp với giá trị đã truyền.

### Bước 4: Kiểm tra Cảnh báo Telegram
**Kỳ vọng:**
- [ ] Bot Telegram gửi tin nhắn báo giá cho các sản phẩm có `sale_price < 300,000đ`.

### Bước 5: Kiểm tra Marker Pattern (Gatekeeper)
```sql
SELECT * FROM raw.batch_control WHERE batch_id = 'test_batch_001';
```
**Kỳ vọng:**
- [ ] Xuất hiện dòng dữ liệu với `status = 'DONE'`.
- [ ] `completed_at` ghi nhận chính xác thời điểm Consumer nhận được tin EOF.

---

## 4. Kiểm tra Điều phối (Airflow & dbt)

### Bước 6: Kích hoạt DAG trên Airflow UI
1. Truy cập `localhost:8080`.
2. Tìm DAG `price_ingestion_pipeline_v2`.
3. Nhấn **Trigger DAG**.

**Kỳ vọng:**
- [ ] `run_price_scraper`: Hoàn thành nhanh (Xanh lá).
- [ ] `wait_for_consumer_eof`: Sẽ ở trạng thái "Running" (Poke) cho đến khi Consumer xác nhận nhận đủ dữ liệu.
- [ ] `run_dbt_transform`: Chỉ bắt đầu **SAU KHI** Sensor thành công.

---

## 5. Kiểm tra Kết quả cuối (DWH)

### Bước 7: Kiểm tra bảng Fact trong DWH
```sql
SELECT count(*) FROM dwh.fact_price_snapshots;
```
**Kỳ vọng:**
- [ ] Số lượng bản ghi tăng lên tương ứng với số tin nhắn DATA đã gửi.

---

## Các lỗi thường gặp (Troubleshooting)
- **Sensor Time Out**: Kiểm tra xem Consumer (`stream-processor`) có bị chết không: `docker logs kafka_consumer_worker`.
- **Dbt Error**: Kiểm tra folder `/app/analytics/dbt` đã có file `profiles.yml` (được copy từ mẫu) chưa.
- **Lỗi .env**: Đảm bảo tất cả các biến trong `.env` đã được điền đúng (không dùng giá trị placeholder).
