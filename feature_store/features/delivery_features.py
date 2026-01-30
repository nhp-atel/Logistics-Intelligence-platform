"""Delivery prediction feature computation."""

from dataclasses import dataclass
from typing import Any

from google.cloud import bigquery

from feature_store.config import FeatureStoreConfig


@dataclass
class DeliveryFeatures:
    """Delivery prediction feature computation and retrieval."""

    config: FeatureStoreConfig

    def __post_init__(self):
        self.client = bigquery.Client(project=self.config.gcp_project_id)
        self.dataset = self.config.bq_dataset_features

    def get_features(self, package_id: str) -> dict[str, Any] | None:
        """Get features for a package."""
        query = f"""
            SELECT
                package_id,
                weight_lbs,
                volume_cubic_in,
                service_type,
                origin_region,
                destination_region,
                day_of_week,
                is_weekend,
                is_holiday,
                is_peak_season,
                route_avg_transit_hours_7d,
                route_avg_transit_hours_30d,
                route_on_time_rate_7d,
                actual_transit_hours
            FROM `{self.config.gcp_project_id}.{self.dataset}.ftr_delivery_predictions`
            WHERE package_id = @package_id
            LIMIT 1
        """

        job_config = bigquery.QueryJobConfig(
            query_parameters=[
                bigquery.ScalarQueryParameter("package_id", "STRING", package_id)
            ]
        )

        results = self.client.query(query, job_config=job_config).result()

        for row in results:
            return dict(row)

        return None

    def get_training_data(
        self,
        start_date: str,
        end_date: str,
        limit: int | None = None,
    ) -> list[dict[str, Any]]:
        """Get training data for delivery prediction model."""
        query = f"""
            SELECT
                package_id,
                weight_lbs,
                volume_cubic_in,
                service_type,
                origin_region,
                destination_region,
                day_of_week,
                is_weekend,
                is_holiday,
                is_peak_season,
                route_avg_transit_hours_7d,
                route_avg_transit_hours_30d,
                route_on_time_rate_7d,
                actual_transit_hours,
                is_on_time
            FROM `{self.config.gcp_project_id}.{self.dataset}.ftr_delivery_predictions`
            WHERE created_date BETWEEN @start_date AND @end_date
                AND actual_transit_hours IS NOT NULL
            {"LIMIT " + str(limit) if limit else ""}
        """

        job_config = bigquery.QueryJobConfig(
            query_parameters=[
                bigquery.ScalarQueryParameter("start_date", "DATE", start_date),
                bigquery.ScalarQueryParameter("end_date", "DATE", end_date),
            ]
        )

        results = self.client.query(query, job_config=job_config).result()
        return [dict(row) for row in results]

    def predict_transit_time(
        self,
        weight_lbs: float,
        service_type: str,
        origin_region: str,
        destination_region: str,
        is_weekend: bool = False,
        is_peak_season: bool = False,
    ) -> float:
        """Simple prediction using historical averages."""
        query = f"""
            SELECT
                AVG(actual_transit_hours) as avg_transit,
                STDDEV(actual_transit_hours) as std_transit
            FROM `{self.config.gcp_project_id}.{self.dataset}.ftr_delivery_predictions`
            WHERE service_type = @service_type
                AND origin_region = @origin_region
                AND destination_region = @destination_region
                AND actual_transit_hours IS NOT NULL
        """

        job_config = bigquery.QueryJobConfig(
            query_parameters=[
                bigquery.ScalarQueryParameter("service_type", "STRING", service_type),
                bigquery.ScalarQueryParameter("origin_region", "STRING", origin_region),
                bigquery.ScalarQueryParameter("destination_region", "STRING", destination_region),
            ]
        )

        results = self.client.query(query, job_config=job_config).result()

        for row in results:
            avg_transit = row.avg_transit or 48.0

            # Apply adjustments
            if is_weekend:
                avg_transit *= 1.1
            if is_peak_season:
                avg_transit *= 1.2
            if weight_lbs > 50:
                avg_transit *= 1.05

            return round(avg_transit, 2)

        # Default fallback
        return 48.0
