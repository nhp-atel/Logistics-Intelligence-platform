{{
    config(
        materialized='table',
        partition_by={
            "field": "created_date",
            "data_type": "date"
        }
    )
}}

with deliveries as (
    select * from {{ ref('fact_deliveries') }}
),

dim_date as (
    select * from {{ ref('dim_date') }}
),

-- Calculate route-level historical statistics
route_stats as (
    select
        origin_region,
        destination_region,
        service_type,
        avg(actual_transit_hours) as avg_transit_hours_all,
        stddev(actual_transit_hours) as std_transit_hours_all,
        countif(is_on_time = true) / nullif(countif(is_on_time is not null), 0) as on_time_rate_all
    from deliveries
    where actual_transit_hours is not null
    group by origin_region, destination_region, service_type
),

-- Calculate recent route statistics (7 days)
route_stats_7d as (
    select
        origin_region,
        destination_region,
        service_type,
        avg(actual_transit_hours) as avg_transit_hours_7d,
        stddev(actual_transit_hours) as std_transit_hours_7d,
        countif(is_on_time = true) / nullif(countif(is_on_time is not null), 0) as on_time_rate_7d,
        count(*) as route_volume_7d
    from deliveries
    where created_at >= timestamp_sub(current_timestamp(), interval 7 day)
        and actual_transit_hours is not null
    group by origin_region, destination_region, service_type
),

-- Calculate recent route statistics (30 days)
route_stats_30d as (
    select
        origin_region,
        destination_region,
        service_type,
        avg(actual_transit_hours) as avg_transit_hours_30d,
        stddev(actual_transit_hours) as std_transit_hours_30d,
        countif(is_on_time = true) / nullif(countif(is_on_time is not null), 0) as on_time_rate_30d,
        count(*) as route_volume_30d
    from deliveries
    where created_at >= timestamp_sub(current_timestamp(), interval 30 day)
        and actual_transit_hours is not null
    group by origin_region, destination_region, service_type
),

final as (
    select
        -- Package info
        d.package_id,
        d.created_date,

        -- Package features
        d.weight_lbs,
        d.volume_cubic_in,
        d.service_type,
        d.signature_required,
        d.is_fragile,
        d.is_hazardous,

        -- Route features
        d.origin_state,
        d.origin_region,
        d.destination_state,
        d.destination_region,
        d.route_type,

        -- Time features
        dt.day_of_week,
        dt.is_weekend,
        dt.is_holiday,
        dt.month,
        case when dt.month in (11, 12) then true else false end as is_peak_season,

        -- Historical route features
        coalesce(rs.avg_transit_hours_all, 48) as route_avg_transit_hours_all,
        coalesce(rs.std_transit_hours_all, 12) as route_std_transit_hours_all,
        coalesce(rs.on_time_rate_all, 0.85) as route_on_time_rate_all,

        coalesce(r7.avg_transit_hours_7d, rs.avg_transit_hours_all, 48) as route_avg_transit_hours_7d,
        coalesce(r7.std_transit_hours_7d, rs.std_transit_hours_all, 12) as route_std_transit_hours_7d,
        coalesce(r7.on_time_rate_7d, rs.on_time_rate_all, 0.85) as route_on_time_rate_7d,
        coalesce(r7.route_volume_7d, 0) as route_volume_7d,

        coalesce(r30.avg_transit_hours_30d, rs.avg_transit_hours_all, 48) as route_avg_transit_hours_30d,
        coalesce(r30.on_time_rate_30d, rs.on_time_rate_all, 0.85) as route_on_time_rate_30d,
        coalesce(r30.route_volume_30d, 0) as route_volume_30d,

        -- Target variable (for training)
        d.actual_transit_hours,
        d.is_on_time,

        -- Metadata
        current_timestamp() as _computed_at

    from deliveries d
    left join dim_date dt on d.created_date = dt.full_date
    left join route_stats rs
        on d.origin_region = rs.origin_region
        and d.destination_region = rs.destination_region
        and d.service_type = rs.service_type
    left join route_stats_7d r7
        on d.origin_region = r7.origin_region
        and d.destination_region = r7.destination_region
        and d.service_type = r7.service_type
    left join route_stats_30d r30
        on d.origin_region = r30.origin_region
        and d.destination_region = r30.destination_region
        and d.service_type = r30.service_type
)

select * from final
