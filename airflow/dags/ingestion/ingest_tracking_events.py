"""DAG for ingesting tracking events from GCS to BigQuery."""

from datetime import datetime, timedelta

from airflow import DAG
from airflow.operators.empty import EmptyOperator
from airflow.providers.google.cloud.operators.bigquery import (
    BigQueryInsertJobOperator,
)
from airflow.providers.google.cloud.transfers.gcs_to_bigquery import (
    GCSToBigQueryOperator,
)

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
    dag_id="ingest_tracking_events",
    description="Ingest tracking events from GCS to BigQuery",
    schedule_interval="*/30 * * * *",  # Every 30 minutes
    start_date=datetime(2024, 1, 1),
    catchup=False,
    default_args=default_args,
    tags=["ingestion", "tracking", "events", "raw"],
    doc_md="""
    ## Tracking Events Ingestion DAG

    This DAG ingests tracking events from Google Cloud Storage to BigQuery.
    It runs frequently to capture near real-time tracking data.

    ### Schedule
    Runs every 30 minutes.

    ### Data Sources
    - GCS: `gs://{bucket}/raw/tracking_events/`

    ### Target Tables
    - BigQuery: `raw.tracking_events`
    """,
) as dag:

    start = EmptyOperator(task_id="start")

    # Load tracking events to BigQuery
    load_tracking_events = GCSToBigQueryOperator(
        task_id="load_tracking_events",
        bucket=GCS_BUCKET,
        source_objects=["raw/tracking_events/*.parquet"],
        destination_project_dataset_table=f"{GCP_PROJECT_ID}.{BQ_DATASET_RAW}.tracking_events",
        source_format="PARQUET",
        write_disposition="WRITE_APPEND",
        create_disposition="CREATE_IF_NEEDED",
        autodetect=False,
        schema_fields=[
            {"name": "event_id", "type": "STRING", "mode": "REQUIRED"},
            {"name": "package_id", "type": "STRING", "mode": "REQUIRED"},
            {"name": "location_id", "type": "STRING", "mode": "NULLABLE"},
            {"name": "event_type", "type": "STRING", "mode": "REQUIRED"},
            {"name": "event_timestamp", "type": "TIMESTAMP", "mode": "REQUIRED"},
            {"name": "driver_id", "type": "STRING", "mode": "NULLABLE"},
            {"name": "vehicle_id", "type": "STRING", "mode": "NULLABLE"},
            {"name": "notes", "type": "STRING", "mode": "NULLABLE"},
            {"name": "latitude", "type": "FLOAT64", "mode": "NULLABLE"},
            {"name": "longitude", "type": "FLOAT64", "mode": "NULLABLE"},
        ],
    )

    # Add loaded_at timestamp
    add_loaded_at = BigQueryInsertJobOperator(
        task_id="add_loaded_at",
        configuration={
            "query": {
                "query": f"""
                    UPDATE `{GCP_PROJECT_ID}.{BQ_DATASET_RAW}.tracking_events`
                    SET _loaded_at = CURRENT_TIMESTAMP()
                    WHERE _loaded_at IS NULL
                """,
                "useLegacySql": False,
            }
        },
    )

    # Validate event counts
    validate_events = BigQueryInsertJobOperator(
        task_id="validate_events",
        configuration={
            "query": {
                "query": f"""
                    SELECT
                        COUNT(*) as total_events,
                        COUNT(DISTINCT package_id) as unique_packages,
                        MIN(event_timestamp) as earliest_event,
                        MAX(event_timestamp) as latest_event
                    FROM `{GCP_PROJECT_ID}.{BQ_DATASET_RAW}.tracking_events`
                    WHERE DATE(event_timestamp) = CURRENT_DATE()
                """,
                "useLegacySql": False,
            }
        },
    )

    end = EmptyOperator(task_id="end")

    start >> load_tracking_events >> add_loaded_at >> validate_events >> end
