"""Integration tests for the API."""

import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def client():
    """Create test client."""
    from api.main import app
    return TestClient(app)


class TestHealthEndpoints:
    """Tests for health check endpoints."""

    def test_health_check(self, client):
        """Test health endpoint."""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "timestamp" in data

    def test_readiness_check(self, client):
        """Test readiness endpoint."""
        response = client.get("/health/ready")
        assert response.status_code == 200
        assert response.json()["status"] == "ready"

    def test_liveness_check(self, client):
        """Test liveness endpoint."""
        response = client.get("/health/live")
        assert response.status_code == 200
        assert response.json()["status"] == "alive"


class TestRootEndpoint:
    """Tests for root endpoint."""

    def test_root(self, client):
        """Test root endpoint."""
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert "name" in data
        assert "version" in data
        assert "docs" in data


class TestDeliveryEndpoints:
    """Tests for delivery endpoints (requires mock or BigQuery connection)."""

    def test_get_delivery_requires_auth(self, client):
        """Test that delivery endpoint requires authentication."""
        response = client.get("/api/v1/deliveries/PKG000000000001")
        # Should return 401 without API key
        assert response.status_code == 401

    def test_list_deliveries_requires_auth(self, client):
        """Test that list endpoint requires authentication."""
        response = client.get("/api/v1/deliveries")
        assert response.status_code == 401


class TestTrackingEndpoints:
    """Tests for tracking endpoints."""

    def test_get_tracking_requires_auth(self, client):
        """Test that tracking endpoint requires authentication."""
        response = client.get("/api/v1/tracking/PKG000000000001")
        assert response.status_code == 401


class TestFeatureEndpoints:
    """Tests for feature endpoints."""

    def test_get_customer_features_requires_auth(self, client):
        """Test that features endpoint requires authentication."""
        response = client.get("/api/v1/features/customer/CUST00000001")
        assert response.status_code == 401
