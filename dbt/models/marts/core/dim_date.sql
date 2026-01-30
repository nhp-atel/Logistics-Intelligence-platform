{{
    config(
        materialized='table'
    )
}}

with date_spine as (
    {{ dbt_date.get_date_dimension('2020-01-01', '2030-12-31') }}
),

final as (
    select
        -- Key
        cast(format_date('%Y%m%d', date_day) as int64) as date_key,

        -- Date
        date_day as full_date,

        -- Calendar attributes
        year_number as year,
        quarter_of_year as quarter,
        month_of_year as month,
        month_name,
        week_of_year,
        day_of_week,
        day_of_week_name as day_name,

        -- Flags
        case when day_of_week in (1, 7) then true else false end as is_weekend,

        -- US Holidays (simplified)
        case
            when month_of_year = 1 and day_of_month = 1 then true  -- New Year
            when month_of_year = 7 and day_of_month = 4 then true  -- Independence Day
            when month_of_year = 12 and day_of_month = 25 then true  -- Christmas
            when month_of_year = 11 and day_of_week = 5
                and day_of_month >= 22 and day_of_month <= 28 then true  -- Thanksgiving (approx)
            else false
        end as is_holiday,

        -- Fiscal calendar (assuming fiscal year = calendar year)
        year_number as fiscal_year,
        quarter_of_year as fiscal_quarter,

        -- Prior period calculations
        date_sub(date_day, interval 1 year) as prior_year_date,
        date_sub(date_day, interval 1 month) as prior_month_date,
        date_sub(date_day, interval 7 day) as prior_week_date

    from date_spine
)

select * from final
