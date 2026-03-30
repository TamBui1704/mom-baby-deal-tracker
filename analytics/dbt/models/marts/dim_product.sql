with source as (
    select distinct 
        product_id, 
        product_name,
        brand,
        unit,
        product_link
    from {{ ref('stg_price_data') }}
)

select
    product_id as product_key,
    product_name,
    brand,
    unit,
    product_link
from source
