{{
    config(
        materialized='incremental',
        unique_key='fact_id',
        on_schema_change='append_new_columns'
    )
}}

with staging as (
    select * from {{ ref('stg_price_data') }}
    {% if is_incremental() %}
        -- Chỉ lấy những bản ghi mới hơn bản ghi lớn nhất đang có trong bảng Fact
        where scraped_at > (select max(scraped_at) from {{ this }})
    {% endif %}
),

dim_date as (
    select * from {{ ref('dim_date') }}
),

dim_time as (
    select * from {{ ref('dim_time') }}
),

dim_product as (
    select * from {{ ref('dim_product') }}
),


fact_base as (
    select
        -- Generate a unique ID for each record
        md5(concat(stg.event_id::text, stg.scraped_at::text)) as fact_id,
        
        -- Link to Date Dimension
        to_char(stg.scraped_at, 'YYYYMMDD')::int as date_key,
        
        -- Link to Time Dimension (Hour * 100 + Minute)
        (extract(hour from stg.scraped_at) * 100 + extract(minute from stg.scraped_at))::int as time_key,
        
        -- Link to Product Dimension
        stg.product_id as product_key,
        

        
        stg.sale_price,
        stg.pack_quantity,
        
        -- Tính đơn giá thực tế (True Unit Price)
        round(stg.sale_price::numeric / stg.pack_quantity::numeric, 2) as unit_price,
        
        stg.scraped_at
    from staging stg
),

-- Calculate Is_Lowest_In_Month
lowest_calc as (
    select
        *,
        min(sale_price) over (
            partition by product_key, date_trunc('month', scraped_at)
        ) as min_price_in_month
    from fact_base
),

final as (
    select
        fact_id,
        date_key,
        time_key,
        product_key,
        sale_price,
        pack_quantity,
        unit_price,
        case 
            when sale_price = min_price_in_month then true 
            else false 
        end as is_lowest_in_month,
        scraped_at
    from lowest_calc
)

select * from final
