-- Bài test: Đảm bảo thời gian cào dữ liệu không nằm ở tương lai
-- Nếu có bản ghi nào có thời gian lớn hơn hiện tại, test này sẽ FAIL
select
    fact_id,
    scraped_at
from {{ ref('fact_price_snapshots') }}
where scraped_at > now()
