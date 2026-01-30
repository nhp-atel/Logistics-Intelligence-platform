"""DAG for ingesting raw package data from GCS to BigQuery."""

from datetime import datetime, timedelta

from airflow import DAG
from airflow.operators.empty import EmptyOperator
from airflow.providers.google.cloud.operators.bigquery import (
    BigQueryInsertJobOperator,
)
from airflow.providers.google.cloud.sensors.gcs import GCSObjectExistenceSensor
from airflow.providers.google.cloud.transfers.gcs_to_bigquery import (
    GCSToBigQueryOperator,
)
from airflow.utils.task_group import TaskGroup

# Configuration
GCP_PROJECT_ID = "{{ var.value.gcp_project_id }}"
GCS_BUCKET = "{{ var.value.gcs_bucket_raw }}"
BQ_DATASET_RAW = "{{ var.value.bq_dataset_raw }}"

default_args = {
    "owner": "data-engineering",
    "depends_on_past": False,
    "email_on_failure": True,
    "email_on_retry": False,
    "retries": 3,
    "retry_delay": timedelta(minutes=5),
    "execution_timeout": timedelta(hours=2),
}

with DAG(
    dag_id="ingest_raw_packages",
    description="Ingest raw package data from GCS to BigQuery",
    schedule_interval="0 6 * * *",  # Daily at 6 AM
    start_date=datetime(2024, 1, 1),
    catchup=False,
    default_args=default_args,
    tags=["ingestion", "packages", "raw"],
    doc_md="""
    ## Package Ingestion DAG

    This DAG ingests raw package data from Google Cloud Storage to BigQuery.

    ### Schedule
    Runs daily at 6 AM UTC.

    ### Data Sources
    - GCS: `gs://{bucket}/raw/packages/`

    ### Target Tables
    - BigQuery: `raw.packages`

    ### Error Handling
    - Retries 3 times with 5-minute delay
    - Sends email on failure
    """,
) as dag:

    start = EmptyOperator(task_id="start")

    # Check for new data files
    check_packages_file = GCSObjectExistenceSensor(
        task_id="check_packages_file",
        bucket=GCS_BUCKET,
        object="{{ ds_nodash }}/packages.parquet",
        timeout=300,
        poke_interval=60,
        mode="poke",
        soft_fail=True,
    )

    # Load packages to BigQuery
    load_packages = GCSToBigQueryOperator(
        task_id="load_packages",
        bucket=GCS_BUCKET,
        source_objects=["raw/packages/*.parquet"],
        destination_project_dataset_table=f"{GCP_PROJECT_ID}.{BQ_DATASET_RAW}.packages",
        source_format="PARQUET",
        write_disposition="WRITE_APPEND",
        create_disposition="CREATE_IF_NEEDED",
        autodetect=False,
        schema_fields=[
            {"name": "package_id", "type": "STRING", "mode": "REQUIRED"},
            {"name": "tracking_number", "type": "STRING", "mode": "REQUIRED"},
            {"name": "sender_customer_id", "type": "STRING", "mode": "REQUIRED"},
            {"name": "recipient_customer_id", "type": "STRING", "mode": "REQUIRED"},
            {"name": "origin_location_id", "type": "STRING", "mode": "REQUIRED"},
            {"name": "destination_location_id", "type": "STRING", "mode": "REQUIRED"},
            {"name": "weight_lbs", "type": "FLOAT64", "mode": "REQUIRED"},
            {"name": "length_in", "type": "FLOAT64", "mode": "NULLABLE"},
            {"name": "width_in", "type": "FLOAT64", "mode": "NULLABLE"},
            {"name": "height_in", "type": "FLOAT64", "mode": "NULLABLE"},
            {"name": "volume_cubic_in", "type": "FLOAT64", "mode": "NULLABLE"},
            {"name": "service_type", "type": "STRING", "mode": "REQUIRED"},
            {"name": "created_at", "type": "TIMESTAMP", "mode": "REQUIRED"},
            {"name": "estimated_delivery_date", "type": "DATE", "mode": "REQUIRED"},
            {"name": "actual_delivery_date", "type": "DATE", "mode": "NULLABLE"},
            {"name": "status", "type": "STRING", "mode": "REQUIRED"},
            {"name": "shipping_cost", "type": "FLOAT64", "mode": "NULLABLE"},
            {"name": "declared_value", "type": "FLOAT64", "mode": "NULLABLE"},
            {"name": "signature_required", "type": "BOOLEAN", "mode": "NULLABLE"},
            {"name": "is_fragile", "type": "BOOLEAN", "mode": "NULLABLE"},
            {"name": "is_hazardous", "type": "BOOLEAN", "mode": "NULLABLE"},
            {"name": "special_instructions", "type": "STRING", "mode": "NULLABLE"},
        ],
    )

    # Add loaded_at timestamp
    add_loaded_at = BigQueryInsertJobOperator(
        task_id="add_loaded_at",
        configuration={
            "query": {
                "query": f"""
                    UPDATE `{GCP_PROJECT_ID}.{BQ_DATASET_RAW}.packages`
                    SET _loaded_at = CURRENT_TIMESTAMP()
                    WHERE _loaded_at IS NULL
                """,
                "useLegacySql": False,
            }
        },
    )

    # Deduplicate if needed
    deduplicate_packages = BigQueryInsertJobOperator(
        task_id="deduplicate_packages",
        configuration={
            "query": {
                "query": f"""
                    CREATE OR REPLACE TABLE `{GCP_PROJECT_ID}.{BQ_DATASET_RAW}.packages` AS
                    SELECT * EXCEPT(row_num)
                    FROM (
                        SELECT *,
                            ROW_NUMBER() OVER (
                                PARTITION BY package_id
                                ORDER BY _loaded_at DESC
                            ) as row_num
                        FROM `{GCP_PROJECT_ID}.{BQ_DATASET_RAW}.packages`
                    )
                    WHERE row_num = 1
                """,
                "useLegacySql": False,
            }
        },
    )

    end = EmptyOperator(task_id="end")

    # Define task dependencies
    start >> check_packages_file >> load_packages >> add_loaded_at >> deduplicate_packages >> end
