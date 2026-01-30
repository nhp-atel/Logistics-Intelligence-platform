"""DAG for computing ML features."""

from datetime import datetime, timedelta

from airflow import DAG
from airflow.operators.empty import EmptyOperator
from airflow.providers.google.cloud.operators.bigquery import (
    BigQueryInsertJobOperator,
)
from airflow.sensors.external_task import ExternalTaskSensor

# Configuration
GCP_PROJECT_ID = "{{ var.value.gcp_project_id }}"
BQ_DATASET_WAREHOUSE = "{{ var.value.bq_dataset_warehouse }}"
BQ_DATASET_FEATURES = "{{ var.value.bq_dataset_features }}"

default_args = {
    "owner": "data-engineering",
    "depends_on_past": False,
    "email_on_failure": True,
    "email_on_retry": False,
    "retries": 2,
    "retry_delay": timedelta(minutes=5),
    "execution_timeout": timedelta(hours=2),
}

with DAG(
    dag_id="compute_features",
    description="Compute ML features for delivery prediction and customer analytics",
    schedule_interval="0 9 * * *",  # Daily at 9 AM (after quality checks)
    start_date=datetime(2024, 1, 1),
    catchup=False,
    default_args=default_args,
    tags=["features", "ml", "analytics"],
    doc_md="""
    ## Feature Computation DAG

    This DAG computes ML features for:
    - Delivery time prediction
    - Customer segmentation
    - Route performance analysis

    ### Schedule
    Runs daily at 9 AM UTC, after data quality checks.

    ### Feature Tables
    - `features.ftr_delivery_predictions` - Features for delivery time prediction
    - `features.ftr_customer_segments` - Customer behavior features
    - `features.ftr_route_performance` - Route optimization features
    """,
) as dag:

    start = EmptyOperator(task_id="start")

    # Wait for quality checks
    wait_for_quality = ExternalTaskSensor(
        task_id="wait_for_quality",
        external_dag_id="data_quality_checks",
        external_task_id="end",
        allowed_states=["success"],
        failed_states=["failed", "skipped"],
        timeout=3600,
        poke_interval=60,
        mode="reschedule",
    )

    # Compute delivery prediction features
    compute_delivery_features = BigQueryInsertJobOperator(
        task_id="compute_delivery_features",
        configuration={
            "query": {
                "query": f"""
                    CREATE OR REPLACE TABLE `{GCP_PROJECT_ID}.{BQ_DATASET_FEATURES}.ftr_delivery_predictions` AS
                    WITH package_stats AS (
                        SELECT
                            p.package_id,
                            p.weight_lbs,
                            p.volume_cubic_in,
                            p.service_type,
                            p.created_at,
                            p.estimated_delivery_date,
                            p.actual_delivery_date,

                            -- Origin and destination
                            origin.state as origin_state,
                            origin.region as origin_region,
                            dest.state as destination_state,
                            dest.region as destination_region,

                            -- Time features
                            EXTRACT(DAYOFWEEK FROM p.created_at) as day_of_week,
                            CASE WHEN EXTRACT(DAYOFWEEK FROM p.created_at) IN (1, 7) THEN TRUE ELSE FALSE END as is_weekend,
                            EXTRACT(MONTH FROM p.created_at) as month,
                            CASE WHEN EXTRACT(MONTH FROM p.created_at) IN (11, 12) THEN TRUE ELSE FALSE END as is_peak_season,

                            -- Calculate transit time
                            TIMESTAMP_DIFF(
                                TIMESTAMP(COALESCE(p.actual_delivery_date, CURRENT_DATE())),
                                p.created_at,
                                HOUR
                            ) as actual_transit_hours

                        FROM `{GCP_PROJECT_ID}.{BQ_DATASET_WAREHOUSE}.fact_deliveries` p
                        LEFT JOIN `{GCP_PROJECT_ID}.{BQ_DATASET_WAREHOUSE}.dim_locations` origin
                            ON p.origin_location_id = origin.location_id
                        LEFT JOIN `{GCP_PROJECT_ID}.{BQ_DATASET_WAREHOUSE}.dim_locations` dest
                            ON p.destination_location_id = dest.location_id
                    ),
                    route_stats AS (
                        SELECT
                            origin_region,
                            destination_region,
                            service_type,
                            AVG(actual_transit_hours) as avg_transit_hours_7d,
                            STDDEV(actual_transit_hours) as std_transit_hours_7d,
                            COUNT(*) as route_volume_7d
                        FROM package_stats
                        WHERE created_at >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 7 DAY)
                        GROUP BY origin_region, destination_region, service_type
                    )
                    SELECT
                        p.package_id,
                        p.weight_lbs,
                        p.volume_cubic_in,
                        p.service_type,

                        -- Location features
                        p.origin_state,
                        p.origin_region,
                        p.destination_state,
                        p.destination_region,

                        -- Time features
                        p.day_of_week,
                        p.is_weekend,
                        p.month,
                        p.is_peak_season,

                        -- Route historical features
                        COALESCE(r.avg_transit_hours_7d, 48) as route_avg_transit_hours_7d,
                        COALESCE(r.std_transit_hours_7d, 12) as route_std_transit_hours_7d,
                        COALESCE(r.route_volume_7d, 0) as route_volume_7d,

                        -- Target (for training)
                        p.actual_transit_hours,

                        -- Metadata
                        CURRENT_TIMESTAMP() as _computed_at

                    FROM package_stats p
                    LEFT JOIN route_stats r
                        ON p.origin_region = r.origin_region
                        AND p.destination_region = r.destination_region
                        AND p.service_type = r.service_type
                """,
                "useLegacySql": False,
                "writeDisposition": "WRITE_TRUNCATE",
            }
        },
    )

    # Compute customer segment features
    compute_customer_features = BigQueryInsertJobOperator(
        task_id="compute_customer_features",
        configuration={
            "query": {
                "query": f"""
                    CREATE OR REPLACE TABLE `{GCP_PROJECT_ID}.{BQ_DATASET_FEATURES}.ftr_customer_segments` AS
                    WITH customer_orders AS (
                        SELECT
                            sender_customer_id as customer_id,
                            package_id,
                            shipping_cost,
                            service_type,
                            created_at,
                            DATE_DIFF(CURRENT_DATE(), DATE(created_at), DAY) as days_ago
                        FROM `{GCP_PROJECT_ID}.{BQ_DATASET_WAREHOUSE}.fact_deliveries`
                    ),
                    customer_metrics AS (
                        SELECT
                            customer_id,

                            -- Volume metrics
                            COUNTIF(days_ago <= 30) as total_packages_30d,
                            COUNTIF(days_ago <= 90) as total_packages_90d,
                            COUNTIF(days_ago <= 365) as total_packages_365d,
                            COUNT(*) as total_packages_all_time,

                            -- Value metrics
                            SUM(CASE WHEN days_ago <= 30 THEN shipping_cost ELSE 0 END) as total_spend_30d,
                            SUM(CASE WHEN days_ago <= 90 THEN shipping_cost ELSE 0 END) as total_spend_90d,
                            SUM(shipping_cost) as total_spend_all_time,
                            AVG(shipping_cost) as avg_order_value,

                            -- Behavior metrics
                            COUNTIF(service_type = 'EXPRESS') / NULLIF(COUNT(*), 0) as pct_express_shipments,
                            COUNTIF(service_type = 'NEXT_DAY') / NULLIF(COUNT(*), 0) as pct_next_day_shipments,

                            -- Recency
                            MIN(days_ago) as days_since_last_order,
                            DATE_DIFF(
                                MAX(DATE(created_at)),
                                MIN(DATE(created_at)),
                                DAY
                            ) / NULLIF(COUNT(*) - 1, 0) as avg_days_between_orders

                        FROM customer_orders
                        GROUP BY customer_id
                    )
                    SELECT
                        cm.customer_id,

                        -- Volume
                        COALESCE(cm.total_packages_30d, 0) as total_packages_30d,
                        COALESCE(cm.total_packages_90d, 0) as total_packages_90d,
                        COALESCE(cm.total_packages_365d, 0) as total_packages_365d,

                        -- Value
                        COALESCE(cm.total_spend_30d, 0) as total_spend_30d,
                        COALESCE(cm.total_spend_90d, 0) as total_spend_90d,
                        COALESCE(cm.avg_order_value, 0) as avg_order_value,

                        -- Behavior
                        COALESCE(cm.pct_express_shipments, 0) as pct_express_shipments,
                        COALESCE(cm.pct_next_day_shipments, 0) as pct_next_day_shipments,
                        COALESCE(cm.avg_days_between_orders, 0) as avg_days_between_orders,

                        -- Recency
                        COALESCE(cm.days_since_last_order, 999) as days_since_last_order,

                        -- Customer value score (simple RFM-like)
                        (
                            CASE
                                WHEN cm.days_since_last_order <= 30 THEN 3
                                WHEN cm.days_since_last_order <= 90 THEN 2
                                ELSE 1
                            END +
                            CASE
                                WHEN cm.total_packages_365d >= 50 THEN 3
                                WHEN cm.total_packages_365d >= 10 THEN 2
                                ELSE 1
                            END +
                            CASE
                                WHEN cm.total_spend_90d >= 1000 THEN 3
                                WHEN cm.total_spend_90d >= 200 THEN 2
                                ELSE 1
                            END
                        ) / 3.0 as customer_value_score,

                        -- Churn risk (simple heuristic)
                        CASE
                            WHEN cm.days_since_last_order > 180 THEN 0.8
                            WHEN cm.days_since_last_order > 90 THEN 0.5
                            WHEN cm.days_since_last_order > 60 THEN 0.3
                            ELSE 0.1
                        END as churn_risk_score,

                        CURRENT_TIMESTAMP() as _computed_at

                    FROM customer_metrics cm
                """,
                "useLegacySql": False,
                "writeDisposition": "WRITE_TRUNCATE",
            }
        },
    )

    # Compute route performance features
    compute_route_features = BigQueryInsertJobOperator(
        task_id="compute_route_features",
        configuration={
            "query": {
                "query": f"""
                    CREATE OR REPLACE TABLE `{GCP_PROJECT_ID}.{BQ_DATASET_FEATURES}.ftr_route_performance` AS
                    SELECT
                        origin.region as origin_region,
                        dest.region as destination_region,
                        p.service_type,

                        -- Volume
                        COUNT(*) as total_packages,
                        COUNTIF(DATE(p.created_at) >= DATE_SUB(CURRENT_DATE(), INTERVAL 7 DAY)) as packages_7d,
                        COUNTIF(DATE(p.created_at) >= DATE_SUB(CURRENT_DATE(), INTERVAL 30 DAY)) as packages_30d,

                        -- Performance
                        AVG(TIMESTAMP_DIFF(
                            TIMESTAMP(p.actual_delivery_date),
                            p.created_at,
                            HOUR
                        )) as avg_transit_hours,

                        COUNTIF(p.actual_delivery_date <= p.estimated_delivery_date)
                            / NULLIF(COUNTIF(p.actual_delivery_date IS NOT NULL), 0) as on_time_rate,

                        -- Cost
                        AVG(p.shipping_cost) as avg_shipping_cost,
                        SUM(p.shipping_cost) as total_revenue,

                        -- Exceptions
                        COUNTIF(p.status = 'exception') / COUNT(*) as exception_rate,

                        CURRENT_TIMESTAMP() as _computed_at

                    FROM `{GCP_PROJECT_ID}.{BQ_DATASET_WAREHOUSE}.fact_deliveries` p
                    LEFT JOIN `{GCP_PROJECT_ID}.{BQ_DATASET_WAREHOUSE}.dim_locations` origin
                        ON p.origin_location_id = origin.location_id
                    LEFT JOIN `{GCP_PROJECT_ID}.{BQ_DATASET_WAREHOUSE}.dim_locations` dest
                        ON p.destination_location_id = dest.location_id
                    GROUP BY origin.region, dest.region, p.service_type
                """,
                "useLegacySql": False,
                "writeDisposition": "WRITE_TRUNCATE",
            }
        },
    )

    end = EmptyOperator(task_id="end")

    # Define dependencies
    start >> wait_for_quality
    wait_for_quality >> [compute_delivery_features, compute_customer_features, compute_route_features]
    [compute_delivery_features, compute_customer_features, compute_route_features] >> end
