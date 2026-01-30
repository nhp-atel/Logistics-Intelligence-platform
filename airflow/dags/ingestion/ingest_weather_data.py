"""DAG for fetching and ingesting weather data."""

from datetime import datetime, timedelta

from airflow import DAG
from airflow.decorators import task
from airflow.operators.empty import EmptyOperator
from airflow.providers.google.cloud.operators.bigquery import (
    BigQueryInsertJobOperator,
)

# Configuration
GCP_PROJECT_ID = "{{ var.value.gcp_project_id }}"
BQ_DATASET_RAW = "{{ var.value.bq_dataset_raw }}"

default_args = {
    "owner": "data-engineering",
    "depends_on_past": False,
    "email_on_failure": True,
    "email_on_retry": False,
    "retries": 3,
    "retry_delay": timedelta(minutes=10),
    "execution_timeout": timedelta(hours=1),
}

with DAG(
    dag_id="ingest_weather_data",
    description="Fetch and ingest weather data from Open-Meteo API",
    schedule_interval="0 5 * * *",  # Daily at 5 AM
    start_date=datetime(2024, 1, 1),
    catchup=False,
    default_args=default_args,
    tags=["ingestion", "weather", "api"],
    doc_md="""
    ## Weather Data Ingestion DAG

    This DAG fetches weather data from the Open-Meteo API for all hub locations
    and loads it to BigQuery.

    ### Schedule
    Runs daily at 5 AM UTC.

    ### Data Sources
    - Open-Meteo API (free, no API key required)

    ### Target Tables
    - BigQuery: `raw.weather`
    """,
) as dag:

    start = EmptyOperator(task_id="start")

    @task
    def get_hub_locations() -> list[dict]:
        """Fetch hub locations from BigQuery."""
        from google.cloud import bigquery

        client = bigquery.Client()
        query = f"""
            SELECT
                location_id,
                latitude,
                longitude,
                city,
                state
            FROM `{GCP_PROJECT_ID}.{BQ_DATASET_RAW}.locations`
            WHERE location_type IN ('hub', 'distribution_center')
            AND is_active = TRUE
        """
        results = client.query(query).result()
        return [dict(row) for row in results]

    @task
    def fetch_weather_data(locations: list[dict]) -> list[dict]:
        """Fetch weather data from Open-Meteo API."""
        import httpx

        weather_data = []
        today = datetime.now().date()

        for loc in locations:
            try:
                url = "https://api.open-meteo.com/v1/forecast"
                params = {
                    "latitude": loc["latitude"],
                    "longitude": loc["longitude"],
                    "daily": "temperature_2m_max,temperature_2m_min,precipitation_sum,weathercode",
                    "timezone": "auto",
                    "start_date": today.isoformat(),
                    "end_date": today.isoformat(),
                }

                response = httpx.get(url, params=params, timeout=30.0)
                response.raise_for_status()
                data = response.json()

                daily = data.get("daily", {})
                if daily:
                    weather_code = daily.get("weathercode", [0])[0]
                    temp_max = daily.get("temperature_2m_max", [70])[0]
                    temp_min = daily.get("temperature_2m_min", [50])[0]
                    precip = daily.get("precipitation_sum", [0])[0]

                    weather_data.append({
                        "location_id": loc["location_id"],
                        "date": today.isoformat(),
                        "condition": _weather_code_to_condition(weather_code),
                        "temperature_f": round((temp_max + temp_min) / 2 * 9 / 5 + 32, 1),
                        "humidity_pct": 50,  # Not available in basic API
                        "wind_speed_mph": 10.0,  # Not available in basic API
                        "precipitation_in": round(precip / 25.4, 2),
                        "visibility_miles": 10.0,
                        "delay_probability": _get_delay_probability(weather_code),
                        "expected_delay_hours": _get_expected_delay(weather_code),
                    })
            except Exception as e:
                print(f"Error fetching weather for {loc['location_id']}: {e}")
                continue

        return weather_data

    def _weather_code_to_condition(code: int) -> str:
        """Convert WMO weather code to condition string."""
        code_map = {
            0: "clear", 1: "partly_cloudy", 2: "partly_cloudy", 3: "cloudy",
            45: "fog", 48: "fog", 51: "light_rain", 53: "rain", 55: "heavy_rain",
            61: "light_rain", 63: "rain", 65: "heavy_rain", 71: "snow",
            73: "snow", 75: "heavy_snow", 80: "rain", 81: "heavy_rain",
            95: "thunderstorm", 96: "thunderstorm",
        }
        return code_map.get(code, "clear")

    def _get_delay_probability(code: int) -> float:
        """Get delay probability based on weather code."""
        delay_map = {
            0: 0.02, 1: 0.03, 2: 0.05, 3: 0.05, 45: 0.15, 48: 0.15,
            51: 0.10, 53: 0.20, 55: 0.35, 61: 0.10, 63: 0.20, 65: 0.35,
            71: 0.40, 73: 0.50, 75: 0.70, 80: 0.20, 81: 0.35,
            95: 0.50, 96: 0.50,
        }
        return delay_map.get(code, 0.02)

    def _get_expected_delay(code: int) -> float:
        """Get expected delay hours based on weather code."""
        delay_map = {
            0: 0, 1: 0, 2: 0, 3: 0, 45: 2, 48: 2,
            51: 1, 53: 2, 55: 4, 61: 1, 63: 2, 65: 4,
            71: 4, 73: 6, 75: 12, 80: 2, 81: 4,
            95: 6, 96: 6,
        }
        return delay_map.get(code, 0)

    @task
    def load_weather_to_bigquery(weather_data: list[dict]) -> None:
        """Load weather data to BigQuery."""
        from google.cloud import bigquery

        if not weather_data:
            print("No weather data to load")
            return

        client = bigquery.Client()
        table_id = f"{GCP_PROJECT_ID}.{BQ_DATASET_RAW}.weather"

        # Add loaded_at timestamp
        for row in weather_data:
            row["_loaded_at"] = datetime.utcnow().isoformat()

        errors = client.insert_rows_json(table_id, weather_data)
        if errors:
            raise Exception(f"Errors inserting rows: {errors}")

        print(f"Loaded {len(weather_data)} weather records")

    end = EmptyOperator(task_id="end")

    # Define task flow
    locations = get_hub_locations()
    weather = fetch_weather_data(locations)
    load = load_weather_to_bigquery(weather)

    start >> locations >> weather >> load >> end
