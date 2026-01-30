"""DAG for running dbt transformations."""

from datetime import datetime, timedelta

from airflow import DAG
from airflow.operators.bash import BashOperator
from airflow.operators.empty import EmptyOperator
from airflow.sensors.external_task import ExternalTaskSensor

# Configuration
DBT_PROJECT_DIR = "/opt/airflow/dbt"
DBT_PROFILES_DIR = "/opt/airflow/dbt"

default_args = {
    "owner": "data-engineering",
    "depends_on_past": False,
    "email_on_failure": True,
    "email_on_retry": False,
    "retries": 2,
    "retry_delay": timedelta(minutes=5),
    "execution_timeout": timedelta(hours=3),
}

with DAG(
    dag_id="run_dbt_models",
    description="Run dbt transformations for dimensional model",
    schedule_interval="0 7 * * *",  # Daily at 7 AM (after ingestion)
    start_date=datetime(2024, 1, 1),
    catchup=False,
    default_args=default_args,
    tags=["transformation", "dbt", "warehouse"],
    doc_md="""
    ## dbt Transformation DAG

    This DAG runs dbt models to transform raw data into the dimensional model.

    ### Schedule
    Runs daily at 7 AM UTC, after the ingestion DAGs.

    ### Model Layers
    1. **Staging** - Clean and standardize raw data
    2. **Intermediate** - Business logic transformations
    3. **Marts** - Final dimensional model (facts & dimensions)
    4. **Features** - ML feature tables

    ### dbt Commands
    - `dbt deps` - Install packages
    - `dbt run` - Run models
    - `dbt test` - Run tests
    - `dbt docs generate` - Generate documentation
    """,
) as dag:

    start = EmptyOperator(task_id="start")

    # Wait for ingestion to complete
    wait_for_ingestion = ExternalTaskSensor(
        task_id="wait_for_ingestion",
        external_dag_id="ingest_raw_packages",
        external_task_id="end",
        allowed_states=["success"],
        failed_states=["failed", "skipped"],
        timeout=3600,
        poke_interval=60,
        mode="reschedule",
    )

    # Install dbt packages
    dbt_deps = BashOperator(
        task_id="dbt_deps",
        bash_command=f"cd {DBT_PROJECT_DIR} && dbt deps --profiles-dir {DBT_PROFILES_DIR}",
    )

    # Run dbt debug to verify connection
    dbt_debug = BashOperator(
        task_id="dbt_debug",
        bash_command=f"cd {DBT_PROJECT_DIR} && dbt debug --profiles-dir {DBT_PROFILES_DIR}",
    )

    # Run staging models
    dbt_run_staging = BashOperator(
        task_id="dbt_run_staging",
        bash_command=f"""
            cd {DBT_PROJECT_DIR} && \
            dbt run \
                --profiles-dir {DBT_PROFILES_DIR} \
                --select staging.*
        """,
    )

    # Run intermediate models
    dbt_run_intermediate = BashOperator(
        task_id="dbt_run_intermediate",
        bash_command=f"""
            cd {DBT_PROJECT_DIR} && \
            dbt run \
                --profiles-dir {DBT_PROFILES_DIR} \
                --select intermediate.*
        """,
    )

    # Run mart models (facts and dimensions)
    dbt_run_marts = BashOperator(
        task_id="dbt_run_marts",
        bash_command=f"""
            cd {DBT_PROJECT_DIR} && \
            dbt run \
                --profiles-dir {DBT_PROFILES_DIR} \
                --select marts.*
        """,
    )

    # Run feature models
    dbt_run_features = BashOperator(
        task_id="dbt_run_features",
        bash_command=f"""
            cd {DBT_PROJECT_DIR} && \
            dbt run \
                --profiles-dir {DBT_PROFILES_DIR} \
                --select marts.features.*
        """,
    )

    # Run dbt tests
    dbt_test = BashOperator(
        task_id="dbt_test",
        bash_command=f"""
            cd {DBT_PROJECT_DIR} && \
            dbt test \
                --profiles-dir {DBT_PROFILES_DIR}
        """,
    )

    # Generate dbt docs
    dbt_docs = BashOperator(
        task_id="dbt_docs_generate",
        bash_command=f"""
            cd {DBT_PROJECT_DIR} && \
            dbt docs generate \
                --profiles-dir {DBT_PROFILES_DIR}
        """,
    )

    end = EmptyOperator(task_id="end")

    # Define dependencies
    start >> wait_for_ingestion >> dbt_deps >> dbt_debug
    dbt_debug >> dbt_run_staging >> dbt_run_intermediate >> dbt_run_marts
    dbt_run_marts >> dbt_run_features >> dbt_test >> dbt_docs >> end
