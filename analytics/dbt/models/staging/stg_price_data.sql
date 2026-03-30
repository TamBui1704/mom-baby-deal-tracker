
with source as (
    select * from {{ source('public', 'stg_price_events') }}
),

renamed as (
    select
        id as event_id,
        CAST(product_id AS TEXT) as product_id,
        product_name,
        raw_data->>'brand' as brand,
        raw_data->>'unit' as unit,
        COALESCE((raw_data->>'pack_quantity')::int, 1) as pack_quantity,
        raw_data->>'product_link' as product_link,
        sale_price,
        scraped_at,
        consumed_at
    from source
)

select * from renamed
