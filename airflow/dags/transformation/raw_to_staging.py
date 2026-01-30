"""DAG for transforming raw data to staging tables."""

from datetime import datetime, timedelta

from airflow import DAG
from airflow.operators.empty import EmptyOperator
from airflow.providers.google.cloud.operators.bigquery import (
    BigQueryInsertJobOperator,
)
from airflow.sensors.external_task import ExternalTaskSensor

# Configuration
GCP_PROJECT_ID = "{{ var.value.gcp_project_id }}"
BQ_DATASET_RAW = "{{ var.value.bq_dataset_raw }}"
BQ_DATASET_STAGING = "{{ var.value.bq_dataset_staging }}"

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
    dag_id="raw_to_staging",
    description="Transform raw data to staging layer with basic cleaning",
    schedule_interval="0 6,12,18 * * *",  # Three times daily
    start_date=datetime(2024, 1, 1),
    catchup=False,
    default_args=default_args,
    tags=["transformation", "staging"],
    doc_md="""
    ## Raw to Staging DAG

    This DAG performs basic transformations on raw data:
    - Data type standardization
    - Null handling
    - Deduplication
    - Basic validation

    ### Schedule
    Runs three times daily at 6 AM, 12 PM, and 6 PM UTC.
    """,
) as dag:

    start = EmptyOperator(task_id="start")

    # Transform packages
    transform_packages = BigQueryInsertJobOperator(
        task_id="transform_packages",
        configuration={
            "query": {
                "query": f"""
                    CREATE OR REPLACE TABLE `{GCP_PROJECT_ID}.{BQ_DATASET_STAGING}.stg_packages` AS
                    WITH source AS (
                        SELECT
                            *,
                            ROW_NUMBER() OVER (
                                PARTITION BY package_id
                                ORDER BY _loaded_at DESC
                            ) as _row_num
                        FROM `{GCP_PROJECT_ID}.{BQ_DATASET_RAW}.packages`
                    ),
                    deduplicated AS (
                        SELECT * EXCEPT(_row_num)
                        FROM source
                        WHERE _row_num = 1
                    )
                    SELECT
                        -- Primary key
                        package_id,
                        tracking_number,

                        -- Foreign keys
                        sender_customer_id,
                        recipient_customer_id,
                        origin_location_id,
                        destination_location_id,

                        -- Dimensions
                        COALESCE(weight_lbs, 0) as weight_lbs,
                        COALESCE(length_in, 0) as length_in,
                        COALESCE(width_in, 0) as width_in,
                        COALESCE(height_in, 0) as height_in,
                        COALESCE(volume_cubic_in, 0) as volume_cubic_in,

                        -- Service info
                        UPPER(TRIM(service_type)) as service_type,
                        status,

                        -- Dates
                        created_at,
                        DATE(created_at) as created_date,
                        estimated_delivery_date,
                        actual_delivery_date,

                        -- Calculated fields
                        CASE
                            WHEN actual_delivery_date IS NOT NULL
                                AND actual_delivery_date <= estimated_delivery_date
                            THEN TRUE
                            WHEN actual_delivery_date IS NOT NULL
                                AND actual_delivery_date > estimated_delivery_date
                            THEN FALSE
                            ELSE NULL
                        END as is_on_time,

                        DATE_DIFF(
                            COALESCE(actual_delivery_date, CURRENT_DATE()),
                            DATE(created_at),
                            DAY
                        ) as transit_days,

                        -- Cost and value
                        COALESCE(shipping_cost, 0) as shipping_cost,
                        declared_value,

                        -- Flags
                        COALESCE(signature_required, FALSE) as signature_required,
                        COALESCE(is_fragile, FALSE) as is_fragile,
                        COALESCE(is_hazardous, FALSE) as is_hazardous,

                        -- Metadata
                        special_instructions,
                        _loaded_at,
                        CURRENT_TIMESTAMP() as _transformed_at

                    FROM deduplicated
                    WHERE package_id IS NOT NULL
                """,
                "useLegacySql": False,
                "writeDisposition": "WRITE_TRUNCATE",
            }
        },
    )

    # Transform tracking events
    transform_tracking_events = BigQueryInsertJobOperator(
        task_id="transform_tracking_events",
        configuration={
            "query": {
                "query": f"""
                    CREATE OR REPLACE TABLE `{GCP_PROJECT_ID}.{BQ_DATASET_STAGING}.stg_tracking_events` AS
                    WITH source AS (
                        SELECT
                            *,
                            ROW_NUMBER() OVER (
                                PARTITION BY event_id
                                ORDER BY _loaded_at DESC
                            ) as _row_num
                        FROM `{GCP_PROJECT_ID}.{BQ_DATASET_RAW}.tracking_events`
                    ),
                    deduplicated AS (
                        SELECT * EXCEPT(_row_num)
                        FROM source
                        WHERE _row_num = 1
                    ),
                    with_lag AS (
                        SELECT
                            *,
                            LAG(event_timestamp) OVER (
                                PARTITION BY package_id
                                ORDER BY event_timestamp
                            ) as prev_event_timestamp
                        FROM deduplicated
                    )
                    SELECT
                        event_id,
                        package_id,
                        location_id,
                        UPPER(TRIM(event_type)) as event_type,
                        event_timestamp,
                        DATE(event_timestamp) as event_date,
                        EXTRACT(HOUR FROM event_timestamp) as event_hour,

                        -- Time since last event
                        TIMESTAMP_DIFF(
                            event_timestamp,
                            prev_event_timestamp,
                            HOUR
                        ) as hours_since_last_event,

                        -- Driver and vehicle
                        driver_id,
                        vehicle_id,

                        -- Location
                        latitude,
                        longitude,

                        -- Notes
                        notes,

                        -- Metadata
                        _loaded_at,
                        CURRENT_TIMESTAMP() as _transformed_at

                    FROM with_lag
                    WHERE event_id IS NOT NULL
                """,
                "useLegacySql": False,
                "writeDisposition": "WRITE_TRUNCATE",
            }
        },
    )

    # Transform customers
    transform_customers = BigQueryInsertJobOperator(
        task_id="transform_customers",
        configuration={
            "query": {
                "query": f"""
                    CREATE OR REPLACE TABLE `{GCP_PROJECT_ID}.{BQ_DATASET_STAGING}.stg_customers` AS
                    WITH source AS (
                        SELECT
                            *,
                            ROW_NUMBER() OVER (
                                PARTITION BY customer_id
                                ORDER BY _loaded_at DESC
                            ) as _row_num
                        FROM `{GCP_PROJECT_ID}.{BQ_DATASET_RAW}.customers`
                    ),
                    deduplicated AS (
                        SELECT * EXCEPT(_row_num)
                        FROM source
                        WHERE _row_num = 1
                    )
                    SELECT
                        customer_id,
                        LOWER(TRIM(customer_type)) as customer_type,
                        TRIM(name) as name,
                        LOWER(TRIM(email)) as email,
                        REGEXP_REPLACE(phone, r'[^0-9]', '') as phone_normalized,
                        phone as phone_original,

                        -- Address
                        TRIM(address_street) as address_street,
                        TRIM(address_city) as address_city,
                        UPPER(TRIM(address_state)) as address_state,
                        TRIM(address_zip_code) as address_zip_code,
                        UPPER(TRIM(COALESCE(address_country, 'US'))) as address_country,

                        -- Account info
                        created_at,
                        DATE(created_at) as created_date,
                        LOWER(TRIM(tier)) as tier,
                        COALESCE(is_active, TRUE) as is_active,

                        -- Metadata
                        _loaded_at,
                        CURRENT_TIMESTAMP() as _transformed_at

                    FROM deduplicated
                    WHERE customer_id IS NOT NULL
                """,
                "useLegacySql": False,
                "writeDisposition": "WRITE_TRUNCATE",
            }
        },
    )

    # Transform locations
    transform_locations = BigQueryInsertJobOperator(
        task_id="transform_locations",
        configuration={
            "query": {
                "query": f"""
                    CREATE OR REPLACE TABLE `{GCP_PROJECT_ID}.{BQ_DATASET_STAGING}.stg_locations` AS
                    WITH source AS (
                        SELECT
                            *,
                            ROW_NUMBER() OVER (
                                PARTITION BY location_id
                                ORDER BY _loaded_at DESC
                            ) as _row_num
                        FROM `{GCP_PROJECT_ID}.{BQ_DATASET_RAW}.locations`
                    ),
                    deduplicated AS (
                        SELECT * EXCEPT(_row_num)
                        FROM source
                        WHERE _row_num = 1
                    )
                    SELECT
                        location_id,
                        LOWER(TRIM(location_type)) as location_type,
                        TRIM(name) as name,
                        TRIM(address) as address,
                        TRIM(city) as city,
                        UPPER(TRIM(state)) as state,
                        TRIM(zip_code) as zip_code,
                        UPPER(TRIM(COALESCE(country, 'US'))) as country,

                        -- Coordinates
                        latitude,
                        longitude,

                        -- Timezone and region
                        timezone,
                        LOWER(TRIM(region)) as region,

                        -- Status
                        COALESCE(is_active, TRUE) as is_active,

                        -- Metadata
                        _loaded_at,
                        CURRENT_TIMESTAMP() as _transformed_at

                    FROM deduplicated
                    WHERE location_id IS NOT NULL
                """,
                "useLegacySql": False,
                "writeDisposition": "WRITE_TRUNCATE",
            }
        },
    )

    end = EmptyOperator(task_id="end")

    # All transforms can run in parallel
    start >> [transform_packages, transform_tracking_events, transform_customers, transform_locations] >> end
