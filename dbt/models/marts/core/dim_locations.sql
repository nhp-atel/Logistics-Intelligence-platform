{{
    config(
        materialized='table'
    )
}}

with locations as (
    select * from {{ ref('stg_locations') }}
),

final as (
    select
        -- Surrogate key
        {{ dbt_utils.generate_surrogate_key(['location_id']) }} as location_key,

        -- Natural key
        location_id,

        -- Attributes
        location_type,
        name,
        address,
        city,
        state,
        zip_code,
        country,
        latitude,
        longitude,
        timezone,
        region,
        is_active,

        -- Derived fields
        case location_type
            when 'hub' then true
            when 'distribution_center' then true
            else false
        end as is_facility

    from locations
)

select * from final
