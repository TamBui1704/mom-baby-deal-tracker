# 🍼 Mom & Baby Deal Tracker

> Dự án **Data Engineering end-to-end** theo dõi và phân tích biến động giá sản phẩm mẹ & bé trên Tiki — được xây dựng để thể hiện năng lực trên toàn bộ modern data stack.

---

## 🎯 Mục tiêu dự án

Các bậc phụ huynh Việt Nam khi mua sắm hàng thiết yếu (tã, sữa bột, khăn ướt) thường bỏ lỡ cửa sổ flash sale hoặc mua giá cao hơn thực tế do giá cả trên Tiki thay đổi liên tục. Dự án này giải quyết vấn đề đó bằng cách:

- **Tự động thu thập giá** sản phẩm trên Tiki mỗi 15 phút
- **Streaming dữ liệu theo thời gian thực** qua Kafka
- **Biến đổi** dữ liệu thô thành mô hình phân tích star-schema qua dbt
- **Phục vụ** một semantic layer (Cube.dev) cho self-service BI
- **Trực quan hóa** xu hướng giá, deal hời và bất thường giá trên Metabase

Kết quả là một **nền tảng price intelligence tự động hoàn toàn**, có khả năng phát hiện mức giá thấp nhất trong tháng và tương quan giảm giá với thời điểm trong ngày (ví dụ: khung giờ flash sale).

---

## 🏗️ Kiến trúc tổng thể

```
┌─────────────────────────────────────────────────────────────────────────┐
│                     ĐIỀU PHỐI (Airflow)                                 │
│         Lịch chạy mỗi 15 phút · Đồng bộ qua EOF Marker                 │
└────────────────────────────┬────────────────────────────────────────────┘
                             │
                    ┌────────▼────────┐
                    │   THU THẬP      │
                    │   TikiScraper   │
                    │   + Kafka       │
                    │   Producer      │
                    └────────┬────────┘
                             │  Kafka Topic: price_raw
                    ┌────────▼────────┐
                    │  XỬ LÝ LUỒNG   │
                    │  Kafka Consumer │
                    │  (Luôn chạy)    │
                    └────────┬────────┘
                             │  Raw → PostgreSQL
                    ┌────────▼────────────────────────────────┐
                    │         KHO DỮ LIỆU (PostgreSQL)        │
                    │  ┌──────────┐  ┌───────────────────────┐│
                    │  │  raw.*   │  │      marts.*          ││
                    │  │ price_raw│  │  dim_product          ││
                    │  │ batch_   │  │  dim_date             ││
                    │  │ control  │  │  dim_time             ││
                    │  └──────────┘  │  fact_price_snapshots ││
                    │                └───────────────────────┘│
                    └────────┬────────────────────────────────┘
                             │  dbt transformations
                    ┌────────▼────────┐
                    │  SEMANTIC LAYER  │
                    │  (Cube.dev)      │
                    │  Measures, Dims  │
                    │  SQL API         │
                    └────────┬────────┘
                             │  SQL / REST API
                    ┌────────▼────────┐
                    │  TRỰC QUAN HÓA  │
                    │  (Metabase)     │
                    │  Dashboards     │
                    └─────────────────┘
```

---

## 🛠️ Công nghệ sử dụng

| Tầng | Công nghệ | Vai trò |
|---|---|---|
| **Điều phối** | Apache Airflow | Lên lịch DAG, quản lý phụ thuộc task |
| **Thu thập** | Python (confluent-kafka) | Scrape web + Kafka Producer |
| **Nhắn tin** | Apache Kafka (KRaft mode) | Streaming sự kiện theo thời gian thực |
| **Xử lý luồng** | Python Consumer | Kafka → PostgreSQL loader |
| **Kho dữ liệu** | PostgreSQL 15 | Star schema tối ưu cho phân tích |
| **Biến đổi** | dbt (Core) | Incremental SQL model, data lineage |
| **Semantic Layer** | Cube.dev | Định nghĩa metrics tập trung, SQL/REST API |
| **Trực quan hóa** | Metabase | Self-service dashboard |
| **Hạ tầng** | Docker Compose | Toàn bộ môi trường local qua container |

---

## 📐 Mô hình dữ liệu (Star Schema)

Kho dữ liệu áp dụng **Kimball star schema** trong schema `marts`:

```
                    ┌─────────────┐
                    │  dim_date   │
                    │  date_key   │
                    │  year/month │
                    │  day_name   │
                    │  is_weekend │
                    └──────┬──────┘
                           │
┌──────────────┐    ┌──────▼───────────────┐    ┌──────────────┐
│  dim_product │    │  fact_price_snapshots│    │  dim_time    │
│  product_key │◄───│  fact_id (MD5)       │───►│  time_key    │
│  product_name│    │  date_key            │    │  hour_24     │
│  brand       │    │  time_key            │    │  time_slot   │
│  unit        │    │  product_key         │    │  is_flash_   │
│  product_link│    │  sale_price          │    │  sale_frame  │
└──────────────┘    │  unit_price          │    └──────────────┘
                    │  pack_quantity       │
                    │  is_lowest_in_month  │
                    │  scraped_at          │
                    └──────────────────────┘
```

**Các quyết định thiết kế quan trọng:**
- `unit_price` tính bằng công thức `sale_price / pack_quantity` — giúp so sánh công bằng giữa các SKU khác nhau (ví dụ: gói 3 cái vs lẻ từng cái)
- `is_lowest_in_month` sử dụng window function trên phân vùng tháng của từng sản phẩm — phát hiện deal ngay trong warehouse mà không cần bảng cảnh báo riêng
- `fact_price_snapshots` được materialized dưới dạng **incremental dbt model** (`unique_key = fact_id`) — chỉ xử lý các bản ghi mới sau mỗi lần chạy, tối ưu hiệu năng ở quy mô lớn

---

## 🔄 Luồng hoạt động của Pipeline

### Giai đoạn 1 — Thu thập (Airflow trigger mỗi 15 phút)
1. `run_price_scraper` — chạy `TikiScraper` với từ khóa: _Bỉm Huggies, Sữa Meiji, Khăn ướt Moony_
2. Mỗi sự kiện sản phẩm được serialize thành JSON và gửi lên Kafka topic `price_raw`
3. Sau cùng gửi một **EOF Marker** (`type: EOF`) để báo hiệu batch hoàn tất

### Giai đoạn 2 — Xử lý luồng (Consumer luôn chạy)
4. Kafka Consumer liên tục đọc từ `price_raw`
5. Tin DATA → nạp vào bảng `raw.price_raw` trong PostgreSQL
6. Khi nhận EOF → ghi `status=DONE` vào bảng `raw.batch_control`

### Giai đoạn 3 — Đồng bộ (Airflow SqlSensor)
7. `wait_for_consumer_eof` poll `raw.batch_control` mỗi 10 giây đến khi `status=DONE`
8. Ngăn dbt chạy trên dữ liệu chưa đầy đủ — **loại bỏ hoàn toàn race condition**

### Giai đoạn 4 — Biến đổi (dbt TaskGroup, theo thứ tự)
```
staging (stg_price_data)
    └── dimensions (dim_product, dim_date, dim_time)  [song song]
            └── facts (fact_price_snapshots)  [incremental]
                    └── reporting (rpt_daily_deals)
```

### Giai đoạn 5 — Phục vụ (Cube Semantic Layer)
- View `market_intelligence_unified` expose một bề mặt đã join sẵn cho các công cụ BI
- Cube xử lý caching, pre-aggregation, và dịch SQL dialect
- Metabase kết nối qua **Cube SQL API** (cổng 15432) — không cần viết SQL thủ công

---

## 📁 Cấu trúc thư mục

```
mom-baby-deal-tracker/
├── src/
│   ├── producers/
│   │   └── scrapers/
│   │       ├── price_producer.py          # Kafka Producer entrypoint
│   │       └── core/
│   │           ├── __init__.py            # Export TikiScraper
│   │           ├── base_scraper.py        # Abstract class cho scraper
│   │           └── tiki_scraper.py        # Scraper thu thập giá Tiki
│   ├── consumers/
│   │   ├── main_consumer.py               # Kafka Consumer luôn chạy
│   │   └── loaders/                       # Logic ghi dữ liệu vào DB
│   └── common/                            # Shared utilities
├── orchestration/
│   └── dags/
│       └── price_ingestion.py             # Airflow DAG (EOF sync pattern)
├── analytics/
│   ├── dbt/
│   │   ├── dbt_project.yml                # Cấu hình dbt project
│   │   ├── profiles.yml                   # Kết nối DB cho dbt
│   │   ├── macros/
│   │   │   ├── generate_schema_name.sql   # Custom schema routing
│   │   │   └── check_table_collision.sql  # Kiểm tra xung đột bảng
│   │   ├── models/
│   │   │   ├── staging/
│   │   │   │   ├── src_postgres.yml       # Khai báo source
│   │   │   │   └── stg_price_data.sql     # Làm sạch dữ liệu thô
│   │   │   └── marts/
│   │   │       ├── schema.yml             # Test & documentation
│   │   │       ├── dim_product.sql        # Dimension sản phẩm
│   │   │       ├── dim_date.sql           # Dimension ngày
│   │   │       ├── dim_time.sql           # Dimension giờ (flash sale frame)
│   │   │       ├── fact_price_snapshots.sql  # Fact table incremental
│   │   │       └── reporting/
│   │   │           └── rpt_daily_deals.sql   # Báo cáo deal hàng ngày
│   │   └── tests/
│   │       ├── assert_sale_price_is_positive.sql  # Giá phải > 0
│   │       ├── assert_scraped_at_is_past.sql      # Thời gian hợp lệ
│   │       └── assert_lowest_price_logic.sql      # Kiểm tra logic deal
│   └── cube/
│       └── schema/
│           ├── cubes/
│           │   ├── fact_price_snapshots.yaml  # Cube fact model
│           │   ├── dim_product.yaml           # Cube product dimension
│           │   ├── dim_date.yaml              # Cube date dimension
│           │   └── dim_time.yaml              # Cube time dimension
│           └── views/
│               └── market_intelligence.yaml   # Unified view cho BI
├── db_init/
│   └── init.sql                           # Khởi tạo schema PostgreSQL
├── deployments/
│   └── docker/
│       └── airflow/
│           └── Dockerfile                 # Custom Airflow image (+ Kafka libs)
├── docs/
│   ├── airflow_orchestration_guide.md     # Hướng dẫn DAG & orchestration
│   ├── dashboard_framework.md             # Thiết kế dashboard Metabase
│   ├── metabase_guide.md                  # Hướng dẫn kết nối Metabase–Cube
│   ├── testing_guide.md                   # Chiến lược test dbt
│   └── test_scenarios.md                  # Kịch bản kiểm thử
├── docker-compose.yml                     # Full stack: 7 services
├── .env.example                           # Template biến môi trường
├── .gitignore
├── Dockerfile                             # Base image chung
└── requirement.txt                        # Python dependencies
```

---

## 🚀 Hướng dẫn chạy

### Yêu cầu
- Docker Desktop ≥ 24.x
- Git

### 1. Clone & cấu hình
```bash
git clone https://github.com/<your-username>/mom-baby-deal-tracker.git
cd mom-baby-deal-tracker
cp .env.example .env
# Chỉnh sửa .env theo thông tin của bạn
```

### 2. Khởi động toàn bộ hệ thống
```bash
docker compose up -d
```

Lệnh này khởi động **7 container**: PostgreSQL, Kafka (KRaft), Kafka Init, Airflow, Kafka Consumer, Cube và Metabase.

### 3. Truy cập giao diện

| Dịch vụ | Địa chỉ | Thông tin đăng nhập |
|---|---|---|
| Airflow | http://localhost:8080 | Xem file `.env` |
| Metabase | http://localhost:3000 | Thiết lập lần đầu |
| Cube Playground | http://localhost:4000 | — |

### 4. Kích hoạt pipeline
Bật DAG `price_ingestion_pipeline_v2` trong Airflow — hệ thống tự động chạy mỗi 15 phút.

---

## 💡 Điểm nổi bật kỹ thuật

| Pattern | Cách triển khai |
|---|---|
| **EOF Marker đồng bộ** | Ngăn race condition giữa Kafka consumer và dbt |
| **Incremental dbt model** | Chỉ xử lý bản ghi `scraped_at` mới mỗi lần chạy — hiệu quả ở scale lớn |
| **Phát hiện deal bằng window function** | Flag `is_lowest_in_month` tính bằng `MIN() OVER (PARTITION BY ...)` ngay trong warehouse |
| **Chuẩn hóa đơn giá thực tế** | `unit_price = sale_price / pack_quantity` — so sánh chính xác giữa các SKU |
| **Semantic layer trừu tượng** | Cube.dev tách định nghĩa metrics khỏi công cụ BI — một nguồn sự thật duy nhất |
| **Phát hiện khung giờ flash sale** | Dimension `is_flash_sale_frame` trong `dim_time` phân tích deal theo thời gian |
| **Hoàn toàn container hóa** | Không cần cài đặt thêm — môi trường tái tạo được qua Docker Compose |

---

## 📊 Một số phân tích có thể làm

- 📉 **Biểu đồ xu hướng giá** — đơn giá theo thời gian cho từng sản phẩm
- 🔥 **Phát hiện deal** — lọc các bản ghi có `is_lowest_in_month = true`
- 🕐 **Tương quan flash sale** — heatmap giá theo `hour_24` và `day_name`
- 📦 **So sánh thương hiệu** — trung bình `unit_price` giữa các hãng (Huggies vs Bobby)


