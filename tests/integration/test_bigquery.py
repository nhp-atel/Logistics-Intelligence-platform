"""Integration tests for BigQuery service."""

import pytest
from unittest.mock import MagicMock, patch


class TestBigQueryService:
    """Tests for BigQuery service."""

    @pytest.fixture
    def mock_settings(self):
        """Create mock settings."""
        settings = MagicMock()
        settings.gcp_project_id = "test-project"
        settings.bq_dataset_warehouse = "warehouse"
        settings.bq_dataset_features = "features"
        return settings

    @patch("google.cloud.bigquery.Client")
    def test_service_initialization(self, mock_client, mock_settings):
        """Test service initializes with BigQuery client."""
        from api.services.bigquery_service import BigQueryService

        service = BigQueryService(mock_settings)

        assert service.client is not None
        assert service.warehouse_dataset == "warehouse"
        assert service.features_dataset == "features"

    @patch("google.cloud.bigquery.Client")
    @pytest.mark.asyncio
    async def test_get_delivery_query_structure(self, mock_client, mock_settings):
        """Test delivery query structure."""
        from api.services.bigquery_service import BigQueryService

        # Setup mock
        mock_result = MagicMock()
        mock_result.__iter__ = lambda self: iter([])
        mock_client.return_value.query.return_value.result.return_value = mock_result

        service = BigQueryService(mock_settings)
        result = await service.get_delivery("PKG000000000001")

        # Verify query was called
        mock_client.return_value.query.assert_called_once()

        # Get the query that was called
        call_args = mock_client.return_value.query.call_args
        query = call_args[0][0]

        # Verify query contains expected elements
        assert "package_id" in query
        assert "fact_deliveries" in query
        assert "@package_id" in query

    @patch("google.cloud.bigquery.Client")
    @pytest.mark.asyncio
    async def test_get_tracking_events_query(self, mock_client, mock_settings):
        """Test tracking events query."""
        from api.services.bigquery_service import BigQueryService

        mock_result = MagicMock()
        mock_result.__iter__ = lambda self: iter([])
        mock_client.return_value.query.return_value.result.return_value = mock_result

        service = BigQueryService(mock_settings)
        result = await service.get_tracking_events("PKG000000000001")

        call_args = mock_client.return_value.query.call_args
        query = call_args[0][0]

        assert "fact_tracking_events" in query
        assert "ORDER BY" in query

    @patch("google.cloud.bigquery.Client")
    @pytest.mark.asyncio
    async def test_get_customer_features_query(self, mock_client, mock_settings):
        """Test customer features query."""
        from api.services.bigquery_service import BigQueryService

        mock_result = MagicMock()
        mock_result.__iter__ = lambda self: iter([])
        mock_client.return_value.query.return_value.result.return_value = mock_result

        service = BigQueryService(mock_settings)
        result = await service.get_customer_features("CUST00000001")

        call_args = mock_client.return_value.query.call_args
        query = call_args[0][0]

        assert "ftr_customer_segments" in query
        assert "@customer_id" in query
