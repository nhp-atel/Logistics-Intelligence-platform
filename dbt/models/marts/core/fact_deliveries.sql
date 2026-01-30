{{
    config(
        materialized='incremental',
        unique_key='package_id',
        partition_by={
            "field": "created_date",
            "data_type": "date",
            "granularity": "day"
        },
        cluster_by=['service_type', 'origin_state', 'destination_state']
    )
}}

with deliveries as (
    select * from {{ ref('int_deliveries_enriched') }}
),

dim_customers as (
    select customer_key, customer_id from {{ ref('dim_customers') }}
),

dim_locations as (
    select location_key, location_id from {{ ref('dim_locations') }}
),

dim_drivers as (
    select driver_key, driver_id from {{ ref('dim_drivers') }}
),

dim_date as (
    select date_key, full_date from {{ ref('dim_date') }}
),

final as (
    select
        -- Surrogate keys
        {{ dbt_utils.generate_surrogate_key(['d.package_id']) }} as package_key,

        -- Natural key
        d.package_id,
        d.tracking_number,

        -- Dimension keys
        sender.customer_key as sender_customer_key,
        recipient.customer_key as recipient_customer_key,
        origin_loc.location_key as origin_location_key,
        dest_loc.location_key as destination_location_key,
        driver.driver_key as driver_key,
        ship_date.date_key as ship_date_key,
        delivery_date.date_key as delivery_date_key,

        -- Degenerate dimensions
        d.service_type,
        d.status,
        d.route_type,

        -- Location attributes (for clustering/partitioning)
        d.origin_state,
        d.destination_state,
        d.origin_region,
        d.destination_region,

        -- Facts/measures
        d.weight_lbs,
        d.volume_cubic_in,
        d.transit_days,
        d.actual_transit_hours,
        d.shipping_cost,
        d.declared_value,
        d.total_tracking_events,
        d.exception_count,
        d.days_late,

        -- Flags
        d.is_on_time,
        d.signature_required,
        d.is_fragile,
        d.is_hazardous,

        -- Dates (for partitioning)
        d.created_at,
        d.created_date,
        d.estimated_delivery_date,
        d.actual_delivery_date,
        d.delivered_at,

        -- Metadata
        current_timestamp() as _dbt_updated_at

    from deliveries d
    left join dim_customers sender on d.sender_customer_id = sender.customer_id
    left join dim_customers recipient on d.recipient_customer_id = recipient.customer_id
    left join dim_locations origin_loc on d.origin_location_id = origin_loc.location_id
    left join dim_locations dest_loc on d.destination_location_id = dest_loc.location_id
    left join dim_drivers driver on d.delivery_driver_id = driver.driver_id
    left join dim_date ship_date on d.created_date = ship_date.full_date
    left join dim_date delivery_date on d.actual_delivery_date = delivery_date.full_date

    {% if is_incremental() %}
    where d.created_at > (select max(created_at) from {{ this }})
    {% endif %}
)

select * from final
