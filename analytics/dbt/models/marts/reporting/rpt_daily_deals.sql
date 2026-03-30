-- rpt_daily_deals.sql
-- Đây là bảng "Thành phẩm" (OBT) dành cho báo cáo. 
-- Mọi logic Join và Measure phức tạp đã được xử lý sẵn ở đây.

{{ config(materialized='view') }}

with facts as (
    select * from {{ ref('fact_price_snapshots') }}
),

dim_product as (
    select * from {{ ref('dim_product') }}
),

dim_date as (
    select * from {{ ref('dim_date') }}
),

dim_time as (
    select * from {{ ref('dim_time') }}
),

final as (
    select
        -- Thông tin định danh
        f.fact_id,
        p.product_name,
        p.brand,
        p.unit,
        p.product_link,
        
        -- Thông tin thời gian (đã giải mã)
        d.date_day,
        d.day_name as day_of_week,
        d.month,
        t.hour_24 as hour_of_day,
        t.time_slot,
        
        -- Các thông số giá (Measures)
        f.sale_price,
        f.unit_price,
        f.is_lowest_in_month,
        
        -- Tính toán thêm: Độ lệch giá so với giá thấp nhất trong tháng
        -- Giúp DA biết deal này đang "hời" bao nhiêu % so với đáy
        case 
            when f.sale_price > 0 
            then round(((f.sale_price - (select min(sale_price) from facts f2 where f2.product_key = f.product_key)) 
                 / f.sale_price) * 100, 2)
            else 0
        end as price_above_floor_pct,
        
        f.scraped_at
    from facts f
    left join dim_product p on f.product_key = p.product_key
    left join dim_date d on f.date_key = d.date_key
    left join dim_time t on f.time_key = t.time_key
)

select * from final
