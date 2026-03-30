# Hướng Dẫn Test Luồng: Kafka -> Consumer -> PostgreSQL

Cẩm nang này hướng dẫn bạn cách kiểm tra luồng dữ liệu đầy đủ: Producer (cào giá) -> Kafka -> Consumer (lưu dữ liệu) -> PostgreSQL (Database).

## Chuẩn Bị
1.  **Docker Desktop**: Đảm bảo Docker đã khởi động.
2.  **Cài đặt thư viện**: Chạy lệnh sau để cài driver kết nối Database:
    ```powershell
    pip install -r requirement.txt
    ```

---

## Bước 1: Khởi Động Hạ Tầng (Kafka & Postgres)
Mở terminal và chạy lệnh để bật cả Kafka và Database:

```powershell
docker compose up -d warehouse-db message-broker
```

> [!IMPORTANT]
> **Quy tắc an toàn dữ liệu**:
> Hiện tại hệ thống đã được tách biệt:
> - **Schema `raw`**: Chỗ lưu dữ liệu gốc từ Python. dbt không có quyền sửa xóa ở đây.
> - **Schema `staging` / `public`**: Chỗ dbt làm việc.
> Việc tách biệt này giúp bảo đảm dữ liệu thật của bạn không bao giờ bị dbt xóa nhầm nữa.

---

## Bước 2: Chạy Consumer (Lưu Dữ Liệu Vào DB)
Tại terminal thứ nhất, chạy script Consumer. Script này sẽ tự động tạo bảng `staging.stg_price_events` nếu chưa có:

```powershell
python src/consumers/test_consumer.py
```
*Thông báo mong đợi:* `Database initialized...` và `Starting Consumer with DB persistence...`

---

## Bước 3: Chạy Producer (Gửi Dữ Liệu)
Mở terminal thứ hai và chạy script cào giá:

```powershell
python src/producers/scrapers/price_producer.py
```
*Thông báo mong đợi:* `Message delivered to raw_price_events...`

---

## Bước 4: Kiểm Tra Dữ Liệu Trong Database
Sau khi thấy Consumer báo `Received & Saving`, bạn có thể kiểm tra xem dữ liệu đã thực sự vào bảng trong Postgres chưa bằng lệnh sau:

```powershell
docker exec -it warehouse_postgres psql -U dw_admin -d mom_baby_dw -c "SELECT * FROM staging.stg_price_events;"
```

---

## Các Lệnh Hữu Ích Khác

### 1. Kiểm tra số lượng bản ghi đã được lưu:
```powershell
docker exec -it warehouse_postgres psql -U dw_admin -d mom_baby_dw -c "SELECT platform, count(*) FROM staging.stg_price_events GROUP BY platform;"
```

### 2. Xóa sạch dữ liệu bảng để test lại:
```powershell
docker exec -it warehouse_postgres psql -U dw_admin -d mom_baby_dw -c "TRUNCATE TABLE staging.stg_price_events;"
```

### 3. Xem danh sách topic Kafka:
```powershell
docker exec -it kafka_broker kafka-topics.sh --bootstrap-server localhost:9092 --list
```

---

## Bước 5: Build Star Schema Data Warehouse bằng dbt

Sau khi đã có dữ liệu trong `staging.stg_price_events`, chúng ta sẽ dùng dbt để chuyển đổi thành mô hình Star Schema (Fact & Dimensions).

### 1. Di chuyển vào thư mục dbt
Mở terminal và di chuyển đến thư mục chứa project dbt:
```powershell
cd analytics/dbt
```

### 2. Kiểm tra cài đặt
Bạn không cần cài lẻ từng thư viện nếu đã chạy `pip install -r requirement.txt` ở **Bước Chuẩn Bị**. Tuy nhiên, bạn có thể kiểm tra lại bằng lệnh:
```powershell
dbt --version
```

### 3. Kiểm tra kết nối
Chạy lệnh sau để kiểm tra cấu hình dbt có kết nối được với Postgres không:
```powershell
dbt debug --profiles-dir .
```

### 4. Build toàn bộ DWH
Chạy lệnh sau để dbt tự động tạo các bảng Dimension và Fact:
```powershell
dbt run --profiles-dir .
```

> [!TIP]
> **Làm sao để không phải gõ `--profiles-dir .` mỗi lần?**
> Mặc định dbt tìm file `profiles.yml` ở thư mục người dùng (`~/.dbt/`). Vì chúng ta để nó ngay trong project, bạn phải dùng flag trên. 
> Để bỏ qua flag này, bạn có thể:
> 1. Copy file `profiles.yml` vào thư mục `C:\Users\<Tên_Bạn>\.dbt\`.
> 2. Hoặc chạy lệnh này một lần trong terminal (chỉ có tác dụng trong phiên terminal đó): `$env:DBT_PROFILES_DIR="."`

---

## Bước 6: Kiểm Tra Kết Quả Trong DWH

Dữ liệu lúc này đã được tổ chức lại theo mô hình Star Schema. Bạn có thể query để kiểm tra:

### 1. Kiểm tra Fact Table (Ảnh chụp giá theo thời gian):
```powershell
docker exec -it warehouse_postgres psql -U dw_admin -d mom_baby_dw -c "SELECT fact_id, date_key, time_key, sale_price, is_lowest_in_month FROM fact_price_snapshots LIMIT 10;"
```

### 2. Kiểm tra Dim Time (Bảng 1440 phút):
```powershell
docker exec -it warehouse_postgres psql -U dw_admin -d mom_baby_dw -c "SELECT * FROM dim_time ORDER BY time_key LIMIT 5;"
```

---

## Quy Tắc An Toàn Dữ Liệu Trong Môi Trường Chuyên Nghiệp

Để ngăn chặn tuyệt đối việc `dbt` xóa nhầm dữ liệu của dự án khác, các kỹ sư dữ liệu thường áp dụng các "Bức tường bảo vệ" sau:

### 1. Phân quyền Database (Cách an toàn nhất)
Thay vì dùng chung một User `dw_admin` có toàn quyền, hãy tạo riêng một User cho dbt với quyền hạn bị giới hạn:
- **Trên Schema `raw` (Dữ liệu gốc)**: Chỉ cấp quyền `SELECT`. dbt sẽ **không bao giờ** có quyền chạy lệnh `DROP` hay `DELETE` ở đây. Nếu dbt cố tình làm vậy, Postgres sẽ báo lỗi `Permission Denied`.
- **Trên Schema `staging` và `dwh`**: Cấp quyền `ALL PRIVILEGES` để dbt tự do tạo/xóa bảng.

### 2. Sử dụng Hậu tố Schema cho Lập trình viên (Schema Suffix)
Mỗi thành viên trong đội nên có một bản copy dữ liệu riêng (Ví dụ: `dev_tambui.fact_price`, `dev_anhnemo.fact_price`). Điều này giúp bạn thoải mái chạy dbt mà không sợ ảnh hưởng đến bảng của đồng nghiệp.

### 3. Quy ước đặt tên (Naming Convention)
Sử dụng các tiền tố bắt buộc: `stg_`, `dim_`, `fct_`. Điều này giúp phân biệt rõ đâu là bảng "sống" của hệ thống khác và đâu là bảng "tạm" của dbt.

---

## Các Lệnh dbt Hữu Ích
*   `dbt test --profiles-dir .`: Chạy các bài kiểm tra dữ liệu (ràng buộc, dữ liệu null...).
*   `dbt docs generate --profiles-dir .`: Tạo tài liệu lineage (nguồn gốc dữ liệu).
*   `dbt run --select marts.dim_time --profiles-dir .`: Chỉ chạy riêng một model cụ thể.

---

## Lưu Ý
*   **Dừng Docker**: Chạy `docker compose down`. (Cẩn thận: Lệnh này sẽ xóa dữ liệu nếu bạn chưa cấu hình Volume).
*   **Dừng Script**: Nhấn `Ctrl + C`.
