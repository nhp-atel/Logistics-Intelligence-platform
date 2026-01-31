"""Pytest configuration and fixtures."""

from datetime import datetime

import pytest

from data_generation.config import GenerationConfig


@pytest.fixture
def generation_config() -> GenerationConfig:
    """Create a test generation config."""
    return GenerationConfig(
        num_packages=100,
        num_customers=50,
        num_drivers=10,
        num_vehicles=10,
        num_locations=50,
        random_seed=42,
        start_date=datetime(2024, 1, 1),
        end_date=datetime(2024, 12, 31),
    )


@pytest.fixture
def sample_customer() -> dict:
    """Create a sample customer record."""
    return {
        "customer_id": "CUST00000001",
        "customer_type": "business",
        "name": "Test Company",
        "email": "test@example.com",
        "phone": "555-123-4567",
        "address_street": "123 Main St",
        "address_city": "New York",
        "address_state": "NY",
        "address_zip_code": "10001",
        "address_country": "US",
        "created_at": "2024-01-01T00:00:00",
        "tier": "gold",
        "is_active": True,
    }


@pytest.fixture
def sample_package() -> dict:
    """Create a sample package record."""
    return {
        "package_id": "PKG000000000001",
        "tracking_number": "1ZABCDEFGHIJKLMNOP",
        "sender_customer_id": "CUST00000001",
        "recipient_customer_id": "CUST00000002",
        "origin_location_id": "LOC00000001",
        "destination_location_id": "LOC00000002",
        "weight_lbs": 5.5,
        "length_in": 10.0,
        "width_in": 8.0,
        "height_in": 6.0,
        "volume_cubic_in": 480.0,
        "service_type": "ground",
        "created_at": "2024-06-15T10:30:00",
        "estimated_delivery_date": "2024-06-20",
        "actual_delivery_date": "2024-06-19",
        "status": "delivered",
        "shipping_cost": 12.50,
        "declared_value": 100.0,
        "signature_required": False,
        "is_fragile": False,
        "is_hazardous": False,
        "special_instructions": None,
    }


@pytest.fixture
def sample_tracking_event() -> dict:
    """Create a sample tracking event."""
    return {
        "event_id": "EVT000000000001",
        "package_id": "PKG000000000001",
        "location_id": "LOC00000001",
        "event_type": "picked_up",
        "event_timestamp": "2024-06-15T14:00:00",
        "driver_id": "DRV00000001",
        "vehicle_id": "VEH00000001",
        "notes": None,
        "latitude": 40.7128,
        "longitude": -74.0060,
    }
