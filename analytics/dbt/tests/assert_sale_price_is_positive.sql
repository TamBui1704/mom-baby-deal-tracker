-- Bài test: Đảm bảo giá bán không bao giờ âm hoặc bằng 0
-- Nếu có bản ghi nào giá <= 0, test này sẽ FAIL
select
    fact_id,
    sale_price
from {{ ref('fact_price_snapshots') }}
where sale_price <= 0
