{{
    config(
        materialized='view'
    )
}}

with source as (
    select * from {{ source('raw', 'locations') }}
),

deduplicated as (
    select
        *,
        row_number() over (
            partition by location_id
            order by _loaded_at desc
        ) as _row_num
    from source
),

cleaned as (
    select
        -- Primary key
        location_id,

        -- Location info
        lower(trim(location_type)) as location_type,
        trim(name) as name,
        trim(address) as address,
        trim(city) as city,
        upper(trim(state)) as state,
        trim(zip_code) as zip_code,
        upper(trim(coalesce(country, 'US'))) as country,

        -- Coordinates
        latitude,
        longitude,

        -- Timezone and region
        timezone,
        lower(trim(region)) as region,

        -- Status
        coalesce(is_active, true) as is_active,

        -- Metadata
        _loaded_at

    from deduplicated
    where _row_num = 1
        and location_id is not null
)

select * from cleaned
