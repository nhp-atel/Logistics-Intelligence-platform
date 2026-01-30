{{
    config(
        materialized='view'
    )
}}

with source as (
    select * from {{ source('raw', 'tracking_events') }}
),

deduplicated as (
    select
        *,
        row_number() over (
            partition by event_id
            order by _loaded_at desc
        ) as _row_num
    from source
),

with_lag as (
    select
        *,
        lag(event_timestamp) over (
            partition by package_id
            order by event_timestamp
        ) as prev_event_timestamp
    from deduplicated
    where _row_num = 1
),

cleaned as (
    select
        -- Primary key
        event_id,

        -- Foreign keys
        package_id,
        location_id,
        driver_id,
        vehicle_id,

        -- Event info
        upper(trim(event_type)) as event_type,
        event_timestamp,
        date(event_timestamp) as event_date,
        extract(hour from event_timestamp) as event_hour,

        -- Time since last event
        timestamp_diff(
            event_timestamp,
            prev_event_timestamp,
            hour
        ) as hours_since_last_event,

        -- Location
        latitude,
        longitude,

        -- Notes
        notes,

        -- Metadata
        _loaded_at

    from with_lag
    where event_id is not null
)

select * from cleaned
