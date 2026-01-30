{{
    config(
        materialized='ephemeral'
    )
}}

with packages as (
    select * from {{ ref('stg_packages') }}
),

tracking_events as (
    select * from {{ ref('stg_tracking_events') }}
),

origin_locations as (
    select * from {{ ref('stg_locations') }}
),

dest_locations as (
    select * from {{ ref('stg_locations') }}
),

-- Get first and last events for each package
event_summary as (
    select
        package_id,
        min(event_timestamp) as first_event_at,
        max(event_timestamp) as last_event_at,
        count(*) as total_events,
        countif(event_type like '%EXCEPTION%' or event_type like '%DELAY%') as exception_count
    from tracking_events
    group by package_id
),

-- Get delivery event specifically
delivery_events as (
    select
        package_id,
        event_timestamp as delivered_at,
        driver_id as delivery_driver_id,
        vehicle_id as delivery_vehicle_id,
        latitude as delivery_latitude,
        longitude as delivery_longitude
    from tracking_events
    where event_type = 'DELIVERED'
    qualify row_number() over (partition by package_id order by event_timestamp desc) = 1
),

enriched as (
    select
        -- Package info
        p.package_id,
        p.tracking_number,
        p.sender_customer_id,
        p.recipient_customer_id,

        -- Locations
        p.origin_location_id,
        p.destination_location_id,
        origin.city as origin_city,
        origin.state as origin_state,
        origin.region as origin_region,
        dest.city as destination_city,
        dest.state as destination_state,
        dest.region as destination_region,

        -- Package dimensions
        p.weight_lbs,
        p.volume_cubic_in,

        -- Service and status
        p.service_type,
        p.status,
        p.is_on_time,

        -- Dates
        p.created_at,
        p.created_date,
        p.estimated_delivery_date,
        p.actual_delivery_date,
        p.transit_days,

        -- Cost
        p.shipping_cost,
        p.declared_value,

        -- Flags
        p.signature_required,
        p.is_fragile,
        p.is_hazardous,

        -- Event metrics
        coalesce(e.total_events, 0) as total_tracking_events,
        coalesce(e.exception_count, 0) as exception_count,
        e.first_event_at,
        e.last_event_at,

        -- Delivery details
        d.delivered_at,
        d.delivery_driver_id,
        d.delivery_vehicle_id,

        -- Calculated metrics
        case
            when p.actual_delivery_date is not null and p.estimated_delivery_date is not null
            then date_diff(p.actual_delivery_date, p.estimated_delivery_date, day)
            else null
        end as days_late,

        timestamp_diff(
            coalesce(d.delivered_at, p.last_event_at),
            p.created_at,
            hour
        ) as actual_transit_hours,

        -- Distance estimate (simplified - would use actual geo calculation in production)
        case
            when origin.region = dest.region then 'local'
            when origin.state = dest.state then 'intrastate'
            else 'interstate'
        end as route_type

    from packages p
    left join event_summary e on p.package_id = e.package_id
    left join delivery_events d on p.package_id = d.package_id
    left join origin_locations origin on p.origin_location_id = origin.location_id
    left join dest_locations dest on p.destination_location_id = dest.location_id
)

select * from enriched
