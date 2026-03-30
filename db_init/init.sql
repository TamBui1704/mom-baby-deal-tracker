-- Kịch bản khởi tạo nhiều database cho dự án Mom & Baby
-- File này sẽ tự động chạy khi khởi tạo container Postgres lần đầu tiên

CREATE DATABASE metabase_db;

-- Database chính mom_baby_dw đã được tạo qua biến môi trường POSTGRES_DB
-- Nhưng ta có thể thêm các lệnh grant quyền hoặc tạo schema sẵn ở đây nếu cần
\c mom_baby_dw;
CREATE SCHEMA IF NOT EXISTS raw;
CREATE SCHEMA IF NOT EXISTS staging;
CREATE SCHEMA IF NOT EXISTS dwh;

-- Bảng lưu dữ liệu thô (Data Lake)
CREATE TABLE IF NOT EXISTS raw.stg_price_events (
    id SERIAL PRIMARY KEY,
    batch_id TEXT,
    raw_data JSONB,
    product_id TEXT,
    product_name TEXT,
    sale_price INT,
    scraped_at TIMESTAMP,
    consumed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Bảng điều khiển tín hiệu (Marker Pattern)
CREATE TABLE IF NOT EXISTS raw.batch_control (
    batch_id TEXT PRIMARY KEY,
    status TEXT,
    completed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
