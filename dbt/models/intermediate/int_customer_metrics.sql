{{
    config(
        materialized='ephemeral'
    )
}}

with customers as (
    select * from {{ ref('stg_customers') }}
),

packages_sent as (
    select
        sender_customer_id as customer_id,
        package_id,
        shipping_cost,
        service_type,
        created_at,
        is_on_time
    from {{ ref('stg_packages') }}
),

packages_received as (
    select
        recipient_customer_id as customer_id,
        package_id,
        created_at as received_at
    from {{ ref('stg_packages') }}
    where status = 'delivered'
),

sent_metrics as (
    select
        customer_id,

        -- Lifetime metrics
        count(*) as lifetime_packages_sent,
        sum(shipping_cost) as lifetime_spend,
        avg(shipping_cost) as avg_order_value,

        -- Recent metrics (30 days)
        countif(created_at >= timestamp_sub(current_timestamp(), interval 30 day)) as packages_sent_30d,
        sum(case when created_at >= timestamp_sub(current_timestamp(), interval 30 day) then shipping_cost else 0 end) as spend_30d,

        -- Recent metrics (90 days)
        countif(created_at >= timestamp_sub(current_timestamp(), interval 90 day)) as packages_sent_90d,
        sum(case when created_at >= timestamp_sub(current_timestamp(), interval 90 day) then shipping_cost else 0 end) as spend_90d,

        -- Service preferences
        countif(service_type = 'EXPRESS') / nullif(count(*), 0) as pct_express,
        countif(service_type = 'NEXT_DAY') / nullif(count(*), 0) as pct_next_day,
        countif(service_type = 'GROUND') / nullif(count(*), 0) as pct_ground,

        -- On-time rate
        countif(is_on_time = true) / nullif(countif(is_on_time is not null), 0) as on_time_rate,

        -- First and last order
        min(created_at) as first_order_at,
        max(created_at) as last_order_at

    from packages_sent
    group by customer_id
),

received_metrics as (
    select
        customer_id,
        count(*) as lifetime_packages_received,
        countif(received_at >= timestamp_sub(current_timestamp(), interval 30 day)) as packages_received_30d
    from packages_received
    group by customer_id
),

customer_metrics as (
    select
        c.customer_id,
        c.customer_type,
        c.name,
        c.tier,
        c.is_active,
        c.created_at as customer_created_at,

        -- Sent metrics
        coalesce(s.lifetime_packages_sent, 0) as lifetime_packages_sent,
        coalesce(s.lifetime_spend, 0) as lifetime_spend,
        coalesce(s.avg_order_value, 0) as avg_order_value,
        coalesce(s.packages_sent_30d, 0) as packages_sent_30d,
        coalesce(s.spend_30d, 0) as spend_30d,
        coalesce(s.packages_sent_90d, 0) as packages_sent_90d,
        coalesce(s.spend_90d, 0) as spend_90d,
        coalesce(s.pct_express, 0) as pct_express,
        coalesce(s.pct_next_day, 0) as pct_next_day,
        coalesce(s.pct_ground, 0) as pct_ground,
        s.on_time_rate,
        s.first_order_at,
        s.last_order_at,

        -- Received metrics
        coalesce(r.lifetime_packages_received, 0) as lifetime_packages_received,
        coalesce(r.packages_received_30d, 0) as packages_received_30d,

        -- Calculated metrics
        date_diff(current_date(), date(s.last_order_at), day) as days_since_last_order,

        case
            when s.first_order_at is not null and s.lifetime_packages_sent > 1
            then date_diff(date(s.last_order_at), date(s.first_order_at), day) / nullif(s.lifetime_packages_sent - 1, 0)
            else null
        end as avg_days_between_orders

    from customers c
    left join sent_metrics s on c.customer_id = s.customer_id
    left join received_metrics r on c.customer_id = r.customer_id
)

select * from customer_metrics
