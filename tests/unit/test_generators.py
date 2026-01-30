"""Unit tests for data generators."""

import pytest

from data_generation.config import GenerationConfig
from data_generation.generators import (
    CustomerGenerator,
    DriverGenerator,
    LocationGenerator,
    PackageGenerator,
    TrackingEventGenerator,
    VehicleGenerator,
)


class TestCustomerGenerator:
    """Tests for CustomerGenerator."""

    def test_generate_creates_correct_number(self, generation_config: GenerationConfig):
        """Test that generator creates the configured number of customers."""
        generator = CustomerGenerator(generation_config)
        customers = generator.generate()

        assert len(customers) == generation_config.num_customers

    def test_generate_creates_unique_ids(self, generation_config: GenerationConfig):
        """Test that all customer IDs are unique."""
        generator = CustomerGenerator(generation_config)
        customers = generator.generate()

        ids = [c["customer_id"] for c in customers]
        assert len(ids) == len(set(ids))

    def test_generate_has_required_fields(self, generation_config: GenerationConfig):
        """Test that customers have all required fields."""
        generator = CustomerGenerator(generation_config)
        customers = generator.generate()

        required_fields = [
            "customer_id",
            "customer_type",
            "name",
            "email",
            "tier",
        ]

        for customer in customers[:5]:  # Check first 5
            for field in required_fields:
                assert field in customer

    def test_customer_types_valid(self, generation_config: GenerationConfig):
        """Test that customer types are valid."""
        generator = CustomerGenerator(generation_config)
        customers = generator.generate()

        valid_types = {"business", "residential"}
        for customer in customers:
            assert customer["customer_type"] in valid_types

    def test_tiers_valid(self, generation_config: GenerationConfig):
        """Test that customer tiers are valid."""
        generator = CustomerGenerator(generation_config)
        customers = generator.generate()

        valid_tiers = {"bronze", "silver", "gold", "platinum"}
        for customer in customers:
            assert customer["tier"] in valid_tiers


class TestLocationGenerator:
    """Tests for LocationGenerator."""

    def test_generate_creates_locations(self, generation_config: GenerationConfig):
        """Test that generator creates locations."""
        generator = LocationGenerator(generation_config)
        locations = generator.generate()

        assert len(locations) == generation_config.num_locations

    def test_generate_includes_hubs(self, generation_config: GenerationConfig):
        """Test that generator creates hub locations."""
        generator = LocationGenerator(generation_config)
        locations = generator.generate()
        hub_locations = generator.get_hub_locations()

        assert len(hub_locations) > 0
        for hub in hub_locations:
            assert hub["location_type"] in ["hub", "distribution_center"]

    def test_locations_have_coordinates(self, generation_config: GenerationConfig):
        """Test that locations have latitude and longitude."""
        generator = LocationGenerator(generation_config)
        locations = generator.generate()

        for loc in locations[:5]:
            assert "latitude" in loc
            assert "longitude" in loc
            assert -90 <= loc["latitude"] <= 90
            assert -180 <= loc["longitude"] <= 180


class TestDriverGenerator:
    """Tests for DriverGenerator."""

    def test_generate_creates_drivers(self, generation_config: GenerationConfig):
        """Test that generator creates drivers."""
        hub_ids = ["LOC00000001", "LOC00000002"]
        generator = DriverGenerator(generation_config, hub_ids)
        drivers = generator.generate()

        assert len(drivers) == generation_config.num_drivers

    def test_drivers_have_required_fields(self, generation_config: GenerationConfig):
        """Test that drivers have required fields."""
        hub_ids = ["LOC00000001"]
        generator = DriverGenerator(generation_config, hub_ids)
        drivers = generator.generate()

        required_fields = ["driver_id", "first_name", "last_name", "status"]
        for driver in drivers[:5]:
            for field in required_fields:
                assert field in driver


class TestPackageGenerator:
    """Tests for PackageGenerator."""

    def test_generate_creates_packages(self, generation_config: GenerationConfig):
        """Test that generator creates packages."""
        customer_ids = [f"CUST{i:08d}" for i in range(1, 11)]
        location_ids = [f"LOC{i:08d}" for i in range(1, 21)]
        hub_ids = location_ids[:3]

        generator = PackageGenerator(
            generation_config, customer_ids, location_ids, hub_ids
        )
        packages = generator.generate()

        assert len(packages) == generation_config.num_packages

    def test_packages_have_valid_service_types(self, generation_config: GenerationConfig):
        """Test that packages have valid service types."""
        customer_ids = [f"CUST{i:08d}" for i in range(1, 11)]
        location_ids = [f"LOC{i:08d}" for i in range(1, 21)]
        hub_ids = location_ids[:3]

        generator = PackageGenerator(
            generation_config, customer_ids, location_ids, hub_ids
        )
        packages = generator.generate()

        valid_types = {"ground", "express", "next_day", "freight"}
        for pkg in packages:
            assert pkg["service_type"] in valid_types

    def test_packages_have_positive_weights(self, generation_config: GenerationConfig):
        """Test that packages have positive weights."""
        customer_ids = [f"CUST{i:08d}" for i in range(1, 11)]
        location_ids = [f"LOC{i:08d}" for i in range(1, 21)]
        hub_ids = location_ids[:3]

        generator = PackageGenerator(
            generation_config, customer_ids, location_ids, hub_ids
        )
        packages = generator.generate()

        for pkg in packages:
            assert pkg["weight_lbs"] > 0


class TestTrackingEventGenerator:
    """Tests for TrackingEventGenerator."""

    def test_generate_creates_events(self, generation_config: GenerationConfig):
        """Test that generator creates events for packages."""
        # Create minimal test data
        packages = [
            {
                "package_id": "PKG000000000001",
                "origin_location_id": "LOC00000001",
                "destination_location_id": "LOC00000010",
                "created_at": "2024-06-15T10:00:00",
                "status": "delivered",
            }
        ]
        locations = [
            {"location_id": f"LOC{i:08d}", "latitude": 40.0, "longitude": -74.0}
            for i in range(1, 11)
        ]
        hub_ids = ["LOC00000001", "LOC00000002"]
        driver_ids = ["DRV00000001"]
        vehicle_ids = ["VEH00000001"]

        generator = TrackingEventGenerator(
            generation_config, packages, locations, hub_ids, driver_ids, vehicle_ids
        )
        events = generator.generate()

        assert len(events) > 0

    def test_events_reference_package(self, generation_config: GenerationConfig):
        """Test that events reference their package."""
        packages = [
            {
                "package_id": "PKG000000000001",
                "origin_location_id": "LOC00000001",
                "destination_location_id": "LOC00000010",
                "created_at": "2024-06-15T10:00:00",
                "status": "delivered",
            }
        ]
        locations = [
            {"location_id": f"LOC{i:08d}", "latitude": 40.0, "longitude": -74.0}
            for i in range(1, 11)
        ]
        hub_ids = ["LOC00000001"]
        driver_ids = ["DRV00000001"]
        vehicle_ids = ["VEH00000001"]

        generator = TrackingEventGenerator(
            generation_config, packages, locations, hub_ids, driver_ids, vehicle_ids
        )
        events = generator.generate()

        for event in events:
            assert event["package_id"] == "PKG000000000001"
