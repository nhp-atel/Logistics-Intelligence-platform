{{
    config(
        materialized='table'
    )
}}

with deliveries as (
    select * from {{ ref('fact_deliveries') }}
),

route_metrics as (
    select
        origin_region,
        destination_region,
        service_type,

        -- Volume metrics
        count(*) as total_packages,
        countif(created_at >= timestamp_sub(current_timestamp(), interval 7 day)) as packages_7d,
        countif(created_at >= timestamp_sub(current_timestamp(), interval 30 day)) as packages_30d,
        countif(created_at >= timestamp_sub(current_timestamp(), interval 90 day)) as packages_90d,

        -- Performance metrics
        avg(actual_transit_hours) as avg_transit_hours,
        min(actual_transit_hours) as min_transit_hours,
        max(actual_transit_hours) as max_transit_hours,
        approx_quantiles(actual_transit_hours, 100)[offset(50)] as median_transit_hours,
        approx_quantiles(actual_transit_hours, 100)[offset(90)] as p90_transit_hours,
        stddev(actual_transit_hours) as std_transit_hours,

        -- On-time metrics
        countif(is_on_time = true) as on_time_count,
        countif(is_on_time = false) as late_count,
        countif(is_on_time is not null) as delivered_count,

        -- Exception metrics
        sum(exception_count) as total_exceptions,
        avg(exception_count) as avg_exceptions_per_package,

        -- Cost metrics
        avg(shipping_cost) as avg_shipping_cost,
        sum(shipping_cost) as total_revenue,
        min(shipping_cost) as min_shipping_cost,
        max(shipping_cost) as max_shipping_cost,

        -- Weight metrics
        avg(weight_lbs) as avg_weight_lbs,
        sum(weight_lbs) as total_weight_lbs

    from deliveries
    where actual_transit_hours is not null
    group by origin_region, destination_region, service_type
),

final as (
    select
        -- Route key
        {{ dbt_utils.generate_surrogate_key(['origin_region', 'destination_region', 'service_type']) }} as route_key,

        -- Route attributes
        origin_region,
        destination_region,
        service_type,
        concat(origin_region, ' → ', destination_region) as route_name,

        -- Volume
        total_packages,
        packages_7d,
        packages_30d,
        packages_90d,

        -- Performance
        round(avg_transit_hours, 2) as avg_transit_hours,
        round(median_transit_hours, 2) as median_transit_hours,
        round(p90_transit_hours, 2) as p90_transit_hours,
        round(std_transit_hours, 2) as std_transit_hours,
        round(min_transit_hours, 2) as min_transit_hours,
        round(max_transit_hours, 2) as max_transit_hours,

        -- On-time rate
        on_time_count,
        late_count,
        delivered_count,
        round(on_time_count / nullif(delivered_count, 0), 4) as on_time_rate,

        -- Exception rate
        total_exceptions,
        round(avg_exceptions_per_package, 4) as avg_exceptions_per_package,
        round(total_exceptions / nullif(total_packages, 0), 4) as exception_rate,

        -- Cost
        round(avg_shipping_cost, 2) as avg_shipping_cost,
        round(total_revenue, 2) as total_revenue,

        -- Weight
        round(avg_weight_lbs, 2) as avg_weight_lbs,
        round(total_weight_lbs, 2) as total_weight_lbs,

        -- Derived metrics
        case
            when on_time_count / nullif(delivered_count, 0) >= 0.95 then 'excellent'
            when on_time_count / nullif(delivered_count, 0) >= 0.90 then 'good'
            when on_time_count / nullif(delivered_count, 0) >= 0.80 then 'average'
            else 'needs_improvement'
        end as performance_tier,

        -- Metadata
        current_timestamp() as _computed_at

    from route_metrics
)

select * from final
