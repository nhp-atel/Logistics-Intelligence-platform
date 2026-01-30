{{
    config(
        materialized='incremental',
        unique_key='event_id',
        partition_by={
            "field": "event_date",
            "data_type": "date",
            "granularity": "day"
        },
        cluster_by=['event_type', 'package_id']
    )
}}

with events as (
    select * from {{ ref('stg_tracking_events') }}
),

dim_locations as (
    select location_key, location_id, state, region from {{ ref('dim_locations') }}
),

dim_drivers as (
    select driver_key, driver_id from {{ ref('dim_drivers') }}
),

dim_date as (
    select date_key, full_date from {{ ref('dim_date') }}
),

final as (
    select
        -- Surrogate key
        {{ dbt_utils.generate_surrogate_key(['e.event_id']) }} as event_key,

        -- Natural key
        e.event_id,

        -- Foreign keys
        e.package_id,
        loc.location_key,
        driver.driver_key,
        dt.date_key as event_date_key,

        -- Event attributes
        e.event_type,
        e.event_timestamp,
        e.event_date,
        e.event_hour,

        -- Location attributes (for clustering)
        loc.state as location_state,
        loc.region as location_region,

        -- Measures
        e.hours_since_last_event,

        -- Coordinates
        e.latitude,
        e.longitude,

        -- Notes
        e.notes,

        -- Metadata
        current_timestamp() as _dbt_updated_at

    from events e
    left join dim_locations loc on e.location_id = loc.location_id
    left join dim_drivers driver on e.driver_id = driver.driver_id
    left join dim_date dt on e.event_date = dt.full_date

    {% if is_incremental() %}
    where e.event_timestamp > (select max(event_timestamp) from {{ this }})
    {% endif %}
)

select * from final
