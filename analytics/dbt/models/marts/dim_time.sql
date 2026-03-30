
{{ config(materialized='table') }}

with minutes as (
    -- Generate series of integers from 0 to 1439 (24 * 60 - 1)
    select (row_number() over () - 1) as minute_offset
    from (select 1 from generate_series(1, 1440)) as s
),

time_base as (
    select
        minute_offset,
        (minute_offset / 60)::int as hour_24,
        (minute_offset % 60)::int as minute_val
    from minutes
),

final as (
    select
        (hour_24 * 100 + minute_val) as time_key,
        hour_24,
        minute_val,
        case
            when hour_24 >= 0 and hour_24 < 6 then 'Sáng sớm'
            when hour_24 >= 6 and hour_24 < 12 then 'Sáng'
            when hour_24 >= 12 and hour_24 < 18 then 'Chiều'
            else 'Tối'
        end as time_slot,
        case
            when hour_24 in (0, 9, 12, 21) and minute_val = 0 then true
            else false
        end as is_flash_sale_frame
    from time_base
)

select * from final
