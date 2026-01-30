{{
    config(
        materialized='table'
    )
}}

with customer_metrics as (
    select * from {{ ref('int_customer_metrics') }}
),

final as (
    select
        -- Customer info
        customer_id,
        customer_type,
        tier,

        -- Volume metrics
        packages_sent_30d as total_packages_30d,
        packages_sent_90d as total_packages_90d,
        lifetime_packages_sent as total_packages_all_time,

        -- Value metrics
        spend_30d as total_spend_30d,
        spend_90d as total_spend_90d,
        lifetime_spend as total_spend_all_time,
        avg_order_value,

        -- Behavior metrics
        pct_express as pct_express_shipments,
        pct_next_day as pct_next_day_shipments,
        pct_ground as pct_ground_shipments,
        on_time_rate as pct_on_time_deliveries,
        avg_days_between_orders,
        days_since_last_order,

        -- Service preference
        case
            when pct_next_day >= 0.5 then 'premium'
            when pct_express >= 0.3 then 'express_preferred'
            else 'standard'
        end as preferred_service_tier,

        -- Customer value score (RFM-based)
        (
            -- Recency score (1-5)
            case
                when days_since_last_order <= 7 then 5
                when days_since_last_order <= 30 then 4
                when days_since_last_order <= 90 then 3
                when days_since_last_order <= 180 then 2
                else 1
            end +
            -- Frequency score (1-5)
            case
                when packages_sent_90d >= 50 then 5
                when packages_sent_90d >= 20 then 4
                when packages_sent_90d >= 10 then 3
                when packages_sent_90d >= 3 then 2
                else 1
            end +
            -- Monetary score (1-5)
            case
                when spend_90d >= 5000 then 5
                when spend_90d >= 1000 then 4
                when spend_90d >= 500 then 3
                when spend_90d >= 100 then 2
                else 1
            end
        ) / 3.0 as customer_value_score,

        -- Churn risk score (0-1)
        case
            when days_since_last_order is null then 0.9
            when days_since_last_order > 180 then 0.85
            when days_since_last_order > 90 then 0.6
            when days_since_last_order > 60 then 0.4
            when days_since_last_order > 30 then 0.2
            else 0.05
        end as churn_risk_score,

        -- Customer segment (derived)
        case
            when lifetime_spend >= 10000 and packages_sent_90d >= 20 then 'champion'
            when lifetime_spend >= 5000 and days_since_last_order <= 30 then 'loyal'
            when spend_90d >= 1000 then 'potential_loyalist'
            when days_since_last_order <= 30 then 'recent'
            when days_since_last_order > 90 and lifetime_spend >= 1000 then 'at_risk'
            when days_since_last_order > 180 then 'lost'
            when lifetime_packages_sent <= 1 then 'new'
            else 'regular'
        end as customer_segment,

        -- Metadata
        current_timestamp() as _computed_at

    from customer_metrics
)

select * from final
