"""Customer feature computation."""

from dataclasses import dataclass
from typing import Any

from google.cloud import bigquery

from feature_store.config import FeatureStoreConfig


@dataclass
class CustomerFeatures:
    """Customer feature computation and retrieval."""

    config: FeatureStoreConfig

    def __post_init__(self) -> None:
        self.client = bigquery.Client(project=self.config.gcp_project_id)
        self.dataset = self.config.bq_dataset_features

    def get_features(self, customer_id: str) -> dict[str, Any] | None:
        """Get features for a customer."""
        query = f"""
            SELECT
                customer_id,
                customer_type,
                tier,
                total_packages_30d,
                total_packages_90d,
                total_spend_30d,
                total_spend_90d,
                avg_order_value,
                pct_express_shipments,
                days_since_last_order,
                customer_value_score,
                churn_risk_score,
                customer_segment
            FROM `{self.config.gcp_project_id}.{self.dataset}.ftr_customer_segments`
            WHERE customer_id = @customer_id
            LIMIT 1
        """

        job_config = bigquery.QueryJobConfig(
            query_parameters=[
                bigquery.ScalarQueryParameter("customer_id", "STRING", customer_id)
            ]
        )

        results = self.client.query(query, job_config=job_config).result()

        for row in results:
            return dict(row)

        return None

    def get_batch_features(self, customer_ids: list[str]) -> list[dict[str, Any]]:
        """Get features for multiple customers."""
        if not customer_ids:
            return []

        query = f"""
            SELECT
                customer_id,
                customer_type,
                tier,
                total_packages_30d,
                total_packages_90d,
                total_spend_30d,
                total_spend_90d,
                avg_order_value,
                pct_express_shipments,
                days_since_last_order,
                customer_value_score,
                churn_risk_score,
                customer_segment
            FROM `{self.config.gcp_project_id}.{self.dataset}.ftr_customer_segments`
            WHERE customer_id IN UNNEST(@customer_ids)
        """

        job_config = bigquery.QueryJobConfig(
            query_parameters=[
                bigquery.ArrayQueryParameter("customer_ids", "STRING", customer_ids)
            ]
        )

        results = self.client.query(query, job_config=job_config).result()
        return [dict(row) for row in results]

    def compute_features(self, _lookback_days: int = 30) -> None:
        """Recompute customer features."""
        query = f"""
            CREATE OR REPLACE TABLE `{self.config.gcp_project_id}.{self.dataset}.ftr_customer_segments` AS
            -- Feature computation query (see dbt model for full SQL)
            SELECT
                c.customer_id,
                c.customer_type,
                c.tier,
                -- ... (abbreviated, see dbt model for full implementation)
                CURRENT_TIMESTAMP() as _computed_at
            FROM `{self.config.gcp_project_id}.warehouse.dim_customers` c
        """

        self.client.query(query).result()
