"""BigQuery service for data access."""

from datetime import date
from typing import Any

from google.cloud import bigquery

from api.config import Settings


class BigQueryService:
    """Service for BigQuery data access."""

    def __init__(self, settings: Settings):
        self.settings = settings
        self.client = bigquery.Client(project=settings.gcp_project_id)
        self.warehouse_dataset = settings.bq_dataset_warehouse
        self.features_dataset = settings.bq_dataset_features

    async def get_delivery(self, package_id: str) -> dict[str, Any] | None:
        """Get delivery by package ID."""
        query = f"""
            SELECT
                package_id,
                tracking_number,
                sender_customer_id,
                recipient_customer_id,
                origin_location_id,
                destination_location_id,
                origin_state,
                destination_state,
                service_type,
                status,
                weight_lbs,
                volume_cubic_in,
                shipping_cost,
                created_at,
                estimated_delivery_date,
                actual_delivery_date,
                is_on_time,
                transit_days
            FROM `{self.settings.gcp_project_id}.{self.warehouse_dataset}.fact_deliveries`
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

    async def list_deliveries(
        self,
        status: str | None = None,
        service_type: str | None = None,
        origin_state: str | None = None,
        destination_state: str | None = None,
        start_date: date | None = None,
        end_date: date | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> tuple[list[dict[str, Any]], int]:
        """List deliveries with filters."""
        conditions = ["1=1"]
        params = []

        if status:
            conditions.append("status = @status")
            params.append(bigquery.ScalarQueryParameter("status", "STRING", status))

        if service_type:
            conditions.append("service_type = @service_type")
            params.append(bigquery.ScalarQueryParameter("service_type", "STRING", service_type))

        if origin_state:
            conditions.append("origin_state = @origin_state")
            params.append(bigquery.ScalarQueryParameter("origin_state", "STRING", origin_state))

        if destination_state:
            conditions.append("destination_state = @destination_state")
            params.append(bigquery.ScalarQueryParameter("destination_state", "STRING", destination_state))

        if start_date:
            conditions.append("DATE(created_at) >= @start_date")
            params.append(bigquery.ScalarQueryParameter("start_date", "DATE", start_date))

        if end_date:
            conditions.append("DATE(created_at) <= @end_date")
            params.append(bigquery.ScalarQueryParameter("end_date", "DATE", end_date))

        where_clause = " AND ".join(conditions)

        # Count query
        count_query = f"""
            SELECT COUNT(*) as total
            FROM `{self.settings.gcp_project_id}.{self.warehouse_dataset}.fact_deliveries`
            WHERE {where_clause}
        """

        count_config = bigquery.QueryJobConfig(query_parameters=params)
        count_result = self.client.query(count_query, job_config=count_config).result()
        total = list(count_result)[0].total

        # Data query
        query = f"""
            SELECT
                package_id, tracking_number, sender_customer_id, recipient_customer_id,
                origin_location_id, destination_location_id, origin_state, destination_state,
                service_type, status, weight_lbs, volume_cubic_in, shipping_cost,
                created_at, estimated_delivery_date, actual_delivery_date, is_on_time, transit_days
            FROM `{self.settings.gcp_project_id}.{self.warehouse_dataset}.fact_deliveries`
            WHERE {where_clause}
            ORDER BY created_at DESC
            LIMIT @limit OFFSET @offset
        """

        params.extend([
            bigquery.ScalarQueryParameter("limit", "INT64", limit),
            bigquery.ScalarQueryParameter("offset", "INT64", offset),
        ])

        job_config = bigquery.QueryJobConfig(query_parameters=params)
        results = self.client.query(query, job_config=job_config).result()

        return [dict(row) for row in results], total

    async def get_delivery_summary(
        self,
        start_date: date | None = None,
        end_date: date | None = None,
    ) -> dict[str, Any]:
        """Get aggregate delivery statistics."""
        conditions = ["1=1"]
        params = []

        if start_date:
            conditions.append("DATE(created_at) >= @start_date")
            params.append(bigquery.ScalarQueryParameter("start_date", "DATE", start_date))

        if end_date:
            conditions.append("DATE(created_at) <= @end_date")
            params.append(bigquery.ScalarQueryParameter("end_date", "DATE", end_date))

        where_clause = " AND ".join(conditions)

        query = f"""
            SELECT
                COUNT(*) as total_packages,
                COUNTIF(status = 'delivered') as delivered_count,
                COUNTIF(status = 'in_transit') as in_transit_count,
                COUNTIF(is_on_time = TRUE) / NULLIF(COUNTIF(is_on_time IS NOT NULL), 0) as on_time_rate,
                AVG(transit_days) as avg_transit_days,
                SUM(shipping_cost) as total_revenue,
                AVG(weight_lbs) as avg_weight_lbs
            FROM `{self.settings.gcp_project_id}.{self.warehouse_dataset}.fact_deliveries`
            WHERE {where_clause}
        """

        job_config = bigquery.QueryJobConfig(query_parameters=params)
        results = self.client.query(query, job_config=job_config).result()

        for row in results:
            return dict(row)

        return {}

    async def get_tracking_events(self, package_id: str) -> list[dict[str, Any]]:
        """Get tracking events for a package."""
        query = f"""
            SELECT
                e.event_id,
                e.package_id,
                e.event_type,
                e.event_timestamp,
                e.location_id,
                l.city as location_city,
                l.state as location_state,
                e.driver_id,
                e.notes,
                e.latitude,
                e.longitude
            FROM `{self.settings.gcp_project_id}.{self.warehouse_dataset}.fact_tracking_events` e
            LEFT JOIN `{self.settings.gcp_project_id}.{self.warehouse_dataset}.dim_locations` l
                ON e.location_key = l.location_key
            WHERE e.package_id = @package_id
            ORDER BY e.event_timestamp ASC
        """

        job_config = bigquery.QueryJobConfig(
            query_parameters=[
                bigquery.ScalarQueryParameter("package_id", "STRING", package_id)
            ]
        )

        results = self.client.query(query, job_config=job_config).result()
        return [dict(row) for row in results]

    async def get_latest_tracking_event(self, package_id: str) -> dict[str, Any] | None:
        """Get latest tracking event for a package."""
        events = await self.get_tracking_events(package_id)
        return events[-1] if events else None

    async def get_customer_features(self, customer_id: str) -> dict[str, Any] | None:
        """Get customer features."""
        query = f"""
            SELECT *
            FROM `{self.settings.gcp_project_id}.{self.features_dataset}.ftr_customer_segments`
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

    async def get_route_features(
        self,
        origin_region: str,
        destination_region: str,
        service_type: str,
    ) -> dict[str, Any] | None:
        """Get route features."""
        query = f"""
            SELECT *
            FROM `{self.settings.gcp_project_id}.{self.features_dataset}.ftr_route_performance`
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

    async def get_delivery_features(self, package_id: str) -> dict[str, Any] | None:
        """Get delivery prediction features."""
        query = f"""
            SELECT *
            FROM `{self.settings.gcp_project_id}.{self.features_dataset}.ftr_delivery_predictions`
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
