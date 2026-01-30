"""Route performance feature computation."""

from dataclasses import dataclass
from typing import Any

from google.cloud import bigquery

from feature_store.config import FeatureStoreConfig


@dataclass
class RouteFeatures:
    """Route performance feature computation and retrieval."""

    config: FeatureStoreConfig

    def __post_init__(self):
        self.client = bigquery.Client(project=self.config.gcp_project_id)
        self.dataset = self.config.bq_dataset_features

    def get_features(
        self,
        origin_region: str,
        destination_region: str,
        service_type: str,
    ) -> dict[str, Any] | None:
        """Get features for a route."""
        query = f"""
            SELECT
                origin_region,
                destination_region,
                service_type,
                total_packages,
                packages_7d,
                packages_30d,
                avg_transit_hours,
                median_transit_hours,
                p90_transit_hours,
                on_time_rate,
                exception_rate,
                avg_shipping_cost,
                performance_tier
            FROM `{self.config.gcp_project_id}.{self.dataset}.ftr_route_performance`
            WHERE origin_region = @origin_region
                AND destination_region = @destination_region
                AND service_type = @service_type
            LIMIT 1
        """

        job_config = bigquery.QueryJobConfig(
            query_parameters=[
                bigquery.ScalarQueryParameter("origin_region", "STRING", origin_region),
                bigquery.ScalarQueryParameter("destination_region", "STRING", destination_region),
                bigquery.ScalarQueryParameter("service_type", "STRING", service_type),
            ]
        )

        results = self.client.query(query, job_config=job_config).result()

        for row in results:
            return dict(row)

        return None

    def get_all_routes(self, min_packages: int = 100) -> list[dict[str, Any]]:
        """Get all routes with minimum package volume."""
        query = f"""
            SELECT
                origin_region,
                destination_region,
                service_type,
                total_packages,
                packages_30d,
                avg_transit_hours,
                on_time_rate,
                exception_rate,
                performance_tier
            FROM `{self.config.gcp_project_id}.{self.dataset}.ftr_route_performance`
            WHERE total_packages >= @min_packages
            ORDER BY total_packages DESC
        """

        job_config = bigquery.QueryJobConfig(
            query_parameters=[
                bigquery.ScalarQueryParameter("min_packages", "INT64", min_packages)
            ]
        )

        results = self.client.query(query, job_config=job_config).result()
        return [dict(row) for row in results]

    def get_underperforming_routes(self, on_time_threshold: float = 0.8) -> list[dict[str, Any]]:
        """Get routes performing below threshold."""
        query = f"""
            SELECT
                origin_region,
                destination_region,
                service_type,
                total_packages,
                on_time_rate,
                exception_rate,
                avg_transit_hours,
                performance_tier
            FROM `{self.config.gcp_project_id}.{self.dataset}.ftr_route_performance`
            WHERE on_time_rate < @threshold
                AND total_packages >= 100
            ORDER BY on_time_rate ASC
        """

        job_config = bigquery.QueryJobConfig(
            query_parameters=[
                bigquery.ScalarQueryParameter("threshold", "FLOAT64", on_time_threshold)
            ]
        )

        results = self.client.query(query, job_config=job_config).result()
        return [dict(row) for row in results]
