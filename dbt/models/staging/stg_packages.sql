{{
    config(
        materialized='view'
    )
}}

with source as (
    select * from {{ source('raw', 'packages') }}
),

deduplicated as (
    select
        *,
        row_number() over (
            partition by package_id
            order by _loaded_at desc
        ) as _row_num
    from source
),

cleaned as (
    select
        -- Primary key
        package_id,
        tracking_number,

        -- Foreign keys
        sender_customer_id,
        recipient_customer_id,
        origin_location_id,
        destination_location_id,

        -- Dimensions
        coalesce(weight_lbs, 0) as weight_lbs,
        coalesce(length_in, 0) as length_in,
        coalesce(width_in, 0) as width_in,
        coalesce(height_in, 0) as height_in,
        coalesce(volume_cubic_in, length_in * width_in * height_in, 0) as volume_cubic_in,

        -- Service info
        upper(trim(service_type)) as service_type,
        lower(trim(status)) as status,

        -- Dates
        created_at,
        date(created_at) as created_date,
        estimated_delivery_date,
        actual_delivery_date,

        -- Calculated fields
        case
            when actual_delivery_date is not null
                and actual_delivery_date <= estimated_delivery_date
            then true
            when actual_delivery_date is not null
                and actual_delivery_date > estimated_delivery_date
            then false
            else null
        end as is_on_time,

        date_diff(
            coalesce(actual_delivery_date, current_date()),
            date(created_at),
            day
        ) as transit_days,

        -- Cost and value
        coalesce(shipping_cost, 0) as shipping_cost,
        declared_value,

        -- Flags
        coalesce(signature_required, false) as signature_required,
        coalesce(is_fragile, false) as is_fragile,
        coalesce(is_hazardous, false) as is_hazardous,

        -- Metadata
        special_instructions,
        _loaded_at

    from deduplicated
    where _row_num = 1
        and package_id is not null
)

select * from cleaned
