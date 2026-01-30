{{
    config(
        materialized='table',
        partition_by={
            "field": "valid_from",
            "data_type": "timestamp"
        }
    )
}}

with customer_metrics as (
    select * from {{ ref('int_customer_metrics') }}
),

final as (
    select
        -- Surrogate key
        {{ dbt_utils.generate_surrogate_key(['customer_id']) }} as customer_key,

        -- Natural key
        customer_id,

        -- Attributes
        customer_type,
        name,
        tier,
        is_active,

        -- Metrics (denormalized for performance)
        lifetime_packages_sent,
        lifetime_spend,
        avg_order_value,
        packages_sent_30d,
        spend_30d,
        packages_sent_90d,
        spend_90d,
        pct_express,
        pct_next_day,
        on_time_rate,
        lifetime_packages_received,
        days_since_last_order,
        avg_days_between_orders,

        -- SCD Type 2 fields
        customer_created_at as valid_from,
        cast('9999-12-31' as timestamp) as valid_to,
        true as is_current

    from customer_metrics
)

select * from final
