-- Bài test: Kiểm tra tính đúng đắn của cờ is_lowest_in_month
-- Tìm những sản phẩm được đánh dấu là "thấp nhất tháng" nhưng thực tế 
-- lại có một mức giá khác trong cùng tháng đó thấp hơn nó.
with lowest_flagged as (
    select * 
    from {{ ref('fact_price_snapshots') }}
    where is_lowest_in_month = true
),

actual_min as (
    select 
        product_key,
        date_trunc('month', scraped_at) as month_val,
        min(sale_price) as real_min_price
    from {{ ref('fact_price_snapshots') }}
    group by 1, 2
)

select 
    f.fact_id,
    f.sale_price,
    m.real_min_price
from lowest_flagged f
join actual_min m 
    on f.product_key = m.product_key 
    and date_trunc('month', f.scraped_at) = m.month_val
where f.sale_price > m.real_min_price
