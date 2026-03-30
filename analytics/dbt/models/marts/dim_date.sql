
{{ config(materialized='table') }}

with date_range as (
    select generate_series(
        '2024-01-01'::date,
        '2026-12-31'::date,
        '1 day'::interval
    )::date as date_day
),

final as (
    select
        to_char(date_day, 'YYYYMMDD')::int as date_key,
        date_day,
        extract(year from date_day) as year,
        extract(month from date_day) as month,
        extract(day from date_day) as day,
        to_char(date_day, 'Day') as day_name,
        case 
            when extract(isodow from date_day) in (6, 7) then true 
            else false 
        end as is_weekend
    from date_range
)

select * from final
