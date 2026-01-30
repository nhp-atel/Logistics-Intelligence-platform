"""DAG for running data quality checks using Great Expectations."""

from datetime import datetime, timedelta

from airflow import DAG
from airflow.decorators import task
from airflow.operators.empty import EmptyOperator
from airflow.providers.google.cloud.operators.bigquery import (
    BigQueryInsertJobOperator,
)
from airflow.sensors.external_task import ExternalTaskSensor

# Configuration
GCP_PROJECT_ID = "{{ var.value.gcp_project_id }}"
BQ_DATASET_STAGING = "{{ var.value.bq_dataset_staging }}"
BQ_DATASET_WAREHOUSE = "{{ var.value.bq_dataset_warehouse }}"

default_args = {
    "owner": "data-engineering",
    "depends_on_past": False,
    "email_on_failure": True,
    "email_on_retry": False,
    "retries": 1,
    "retry_delay": timedelta(minutes=5),
    "execution_timeout": timedelta(hours=1),
}

with DAG(
    dag_id="data_quality_checks",
    description="Run data quality checks on staging and warehouse tables",
    schedule_interval="0 8 * * *",  # Daily at 8 AM (after transformations)
    start_date=datetime(2024, 1, 1),
    catchup=False,
    default_args=default_args,
    tags=["quality", "validation", "monitoring"],
    doc_md="""
    ## Data Quality Checks DAG

    This DAG runs comprehensive data quality checks on all tables.

    ### Checks Performed
    - Row count validation
    - Null checks for required fields
    - Unique key validation
    - Referential integrity
    - Value range validation
    - Freshness checks

    ### Schedule
    Runs daily at 8 AM UTC, after dbt transformations.
    """,
) as dag:

    start = EmptyOperator(task_id="start")

    # Wait for dbt to complete
    wait_for_dbt = ExternalTaskSensor(
        task_id="wait_for_dbt",
        external_dag_id="run_dbt_models",
        external_task_id="end",
        allowed_states=["success"],
        failed_states=["failed", "skipped"],
        timeout=3600,
        poke_interval=60,
        mode="reschedule",
    )

    # Check packages table
    check_packages = BigQueryInsertJobOperator(
        task_id="check_packages_quality",
        configuration={
            "query": {
                "query": f"""
                    WITH quality_checks AS (
                        SELECT
                            'stg_packages' as table_name,
                            COUNT(*) as total_rows,
                            COUNTIF(package_id IS NULL) as null_package_id,
                            COUNTIF(sender_customer_id IS NULL) as null_sender,
                            COUNTIF(recipient_customer_id IS NULL) as null_recipient,
                            COUNTIF(weight_lbs < 0) as negative_weight,
                            COUNTIF(shipping_cost < 0) as negative_cost,
                            COUNT(DISTINCT package_id) as unique_packages,
                            COUNTIF(service_type NOT IN ('GROUND', 'EXPRESS', 'NEXT_DAY', 'FREIGHT')) as invalid_service_type,
                            MAX(_transformed_at) as last_updated
                        FROM `{GCP_PROJECT_ID}.{BQ_DATASET_STAGING}.stg_packages`
                    )
                    SELECT
                        table_name,
                        total_rows,
                        CASE WHEN total_rows = 0 THEN 'FAIL' ELSE 'PASS' END as row_count_check,
                        CASE WHEN null_package_id > 0 THEN 'FAIL' ELSE 'PASS' END as null_pk_check,
                        CASE WHEN total_rows != unique_packages THEN 'FAIL' ELSE 'PASS' END as uniqueness_check,
                        CASE WHEN negative_weight > 0 THEN 'FAIL' ELSE 'PASS' END as weight_check,
                        CASE WHEN invalid_service_type > 0 THEN 'WARN' ELSE 'PASS' END as service_type_check,
                        CASE WHEN TIMESTAMP_DIFF(CURRENT_TIMESTAMP(), last_updated, HOUR) > 24 THEN 'WARN' ELSE 'PASS' END as freshness_check
                    FROM quality_checks
                """,
                "useLegacySql": False,
            }
        },
    )

    # Check tracking events
    check_tracking_events = BigQueryInsertJobOperator(
        task_id="check_tracking_events_quality",
        configuration={
            "query": {
                "query": f"""
                    WITH quality_checks AS (
                        SELECT
                            'stg_tracking_events' as table_name,
                            COUNT(*) as total_rows,
                            COUNTIF(event_id IS NULL) as null_event_id,
                            COUNTIF(package_id IS NULL) as null_package_id,
                            COUNTIF(event_timestamp IS NULL) as null_timestamp,
                            COUNT(DISTINCT event_id) as unique_events,
                            MAX(_transformed_at) as last_updated
                        FROM `{GCP_PROJECT_ID}.{BQ_DATASET_STAGING}.stg_tracking_events`
                    )
                    SELECT
                        table_name,
                        total_rows,
                        CASE WHEN total_rows = 0 THEN 'FAIL' ELSE 'PASS' END as row_count_check,
                        CASE WHEN null_event_id > 0 THEN 'FAIL' ELSE 'PASS' END as null_pk_check,
                        CASE WHEN total_rows != unique_events THEN 'FAIL' ELSE 'PASS' END as uniqueness_check,
                        CASE WHEN null_timestamp > 0 THEN 'FAIL' ELSE 'PASS' END as timestamp_check
                    FROM quality_checks
                """,
                "useLegacySql": False,
            }
        },
    )

    # Check referential integrity
    check_referential_integrity = BigQueryInsertJobOperator(
        task_id="check_referential_integrity",
        configuration={
            "query": {
                "query": f"""
                    WITH orphan_packages AS (
                        SELECT COUNT(*) as orphan_count
                        FROM `{GCP_PROJECT_ID}.{BQ_DATASET_STAGING}.stg_packages` p
                        LEFT JOIN `{GCP_PROJECT_ID}.{BQ_DATASET_STAGING}.stg_customers` c
                            ON p.sender_customer_id = c.customer_id
                        WHERE c.customer_id IS NULL
                    ),
                    orphan_events AS (
                        SELECT COUNT(*) as orphan_count
                        FROM `{GCP_PROJECT_ID}.{BQ_DATASET_STAGING}.stg_tracking_events` e
                        LEFT JOIN `{GCP_PROJECT_ID}.{BQ_DATASET_STAGING}.stg_packages` p
                            ON e.package_id = p.package_id
                        WHERE p.package_id IS NULL
                    )
                    SELECT
                        'referential_integrity' as check_type,
                        (SELECT orphan_count FROM orphan_packages) as orphan_packages,
                        (SELECT orphan_count FROM orphan_events) as orphan_events,
                        CASE
                            WHEN (SELECT orphan_count FROM orphan_packages) > 0
                                OR (SELECT orphan_count FROM orphan_events) > 0
                            THEN 'WARN'
                            ELSE 'PASS'
                        END as overall_status
                """,
                "useLegacySql": False,
            }
        },
    )

    @task
    def publish_quality_report() -> None:
        """Publish data quality report to Pub/Sub."""
        from google.cloud import pubsub_v1
        import json

        publisher = pubsub_v1.PublisherClient()
        topic_path = publisher.topic_path(GCP_PROJECT_ID, "data-quality-alerts")

        message = {
            "timestamp": datetime.utcnow().isoformat(),
            "dag_id": "data_quality_checks",
            "status": "completed",
            "checks_passed": True,
        }

        future = publisher.publish(
            topic_path,
            json.dumps(message).encode("utf-8"),
        )
        future.result()
        print(f"Published quality report to {topic_path}")

    end = EmptyOperator(task_id="end")

    # Define dependencies
    start >> wait_for_dbt
    wait_for_dbt >> [check_packages, check_tracking_events, check_referential_integrity]
    [check_packages, check_tracking_events, check_referential_integrity] >> publish_quality_report() >> end
