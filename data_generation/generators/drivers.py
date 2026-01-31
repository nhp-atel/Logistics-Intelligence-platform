"""Driver and vehicle data generators."""

import random
from datetime import timedelta
from typing import Any

from faker import Faker

from data_generation.config import GenerationConfig


class DriverGenerator:
    """Generate synthetic driver data."""

    def __init__(self, config: GenerationConfig, hub_location_ids: list[str]):
        self.config = config
        self.hub_location_ids = hub_location_ids
        self.fake = Faker()
        Faker.seed(config.random_seed)
        random.seed(config.random_seed)

    def generate(self) -> list[dict[str, Any]]:
        """Generate driver records."""
        drivers = []

        for i in range(self.config.num_drivers):
            driver_id = f"DRV{i + 1:08d}"
            driver = self._generate_driver(driver_id, i)
            drivers.append(driver)

        return drivers

    def _generate_driver(self, driver_id: str, _index: int) -> dict[str, Any]:
        """Generate a single driver record."""
        # Generate hire date within a reasonable range (up to 10 years ago)
        max_tenure_days = 365 * 10
        tenure_days = random.randint(30, max_tenure_days)
        hire_date = self.config.end_date - timedelta(days=tenure_days)

        # Driver status based on tenure
        status = "active"
        if random.random() < 0.03:
            status = "on_leave"
        elif random.random() < 0.02:
            status = "inactive"

        # Assign to a hub
        home_facility_id = random.choice(self.hub_location_ids) if self.hub_location_ids else None

        return {
            "driver_id": driver_id,
            "first_name": self.fake.first_name(),
            "last_name": self.fake.last_name(),
            "license_number": self._generate_license_number(),
            "license_state": random.choice(["CA", "TX", "NY", "FL", "IL", "PA", "OH", "GA"]),
            "hire_date": hire_date.date().isoformat(),
            "home_facility_id": home_facility_id,
            "status": status,
            "phone": self.fake.phone_number(),
            "email": self.fake.email(),
            "years_experience": max(1, tenure_days // 365),
            "certifications": self._generate_certifications(),
        }

    def _generate_license_number(self) -> str:
        """Generate a fake driver's license number."""
        letter = random.choice("ABCDEFGHIJKLMNOPQRSTUVWXYZ")
        numbers = "".join([str(random.randint(0, 9)) for _ in range(8)])
        return f"{letter}{numbers}"

    def _generate_certifications(self) -> str:
        """Generate driver certifications."""
        certs = ["CDL-A", "CDL-B", "Hazmat", "Tanker", "Doubles/Triples"]
        num_certs = random.randint(1, 3)
        selected = random.sample(certs, num_certs)
        return ",".join(selected)


class VehicleGenerator:
    """Generate synthetic vehicle data."""

    VEHICLE_TYPES = [
        ("delivery_van", 2000, 0.6),
        ("box_truck", 5000, 0.25),
        ("semi_trailer", 40000, 0.1),
        ("cargo_van", 1500, 0.05),
    ]

    def __init__(self, config: GenerationConfig, hub_location_ids: list[str]):
        self.config = config
        self.hub_location_ids = hub_location_ids
        self.fake = Faker()
        Faker.seed(config.random_seed)
        random.seed(config.random_seed)

    def generate(self) -> list[dict[str, Any]]:
        """Generate vehicle records."""
        vehicles = []

        for i in range(self.config.num_vehicles):
            vehicle_id = f"VEH{i + 1:08d}"
            vehicle = self._generate_vehicle(vehicle_id, i)
            vehicles.append(vehicle)

        return vehicles

    def _generate_vehicle(self, vehicle_id: str, _index: int) -> dict[str, Any]:
        """Generate a single vehicle record."""
        # Select vehicle type based on weights
        types = [t[0] for t in self.VEHICLE_TYPES]
        weights = [t[2] for t in self.VEHICLE_TYPES]
        vehicle_type = random.choices(types, weights=weights, k=1)[0]

        # Get capacity for selected type
        capacity = next(t[1] for t in self.VEHICLE_TYPES if t[0] == vehicle_type)

        # Vehicle year (2015-2024)
        year = random.randint(2015, 2024)

        # Status
        status = "active"
        if random.random() < 0.05:
            status = "maintenance"
        elif random.random() < 0.02:
            status = "retired"

        # Assign to a facility
        assigned_facility_id = random.choice(self.hub_location_ids) if self.hub_location_ids else None

        return {
            "vehicle_id": vehicle_id,
            "vehicle_type": vehicle_type,
            "make": random.choice(["Ford", "Freightliner", "International", "Peterbilt", "Kenworth", "Mercedes"]),
            "model": self._get_model_for_type(vehicle_type),
            "year": year,
            "capacity_lbs": capacity,
            "capacity_cubic_ft": capacity // 10,  # Rough estimate
            "assigned_facility_id": assigned_facility_id,
            "license_plate": self._generate_license_plate(),
            "vin": self._generate_vin(),
            "fuel_type": random.choices(["diesel", "gasoline", "electric"], weights=[0.6, 0.3, 0.1], k=1)[0],
            "status": status,
            "last_maintenance_date": (self.config.end_date - timedelta(days=random.randint(1, 90))).date().isoformat(),
            "mileage": random.randint(10000, 500000),
        }

    def _get_model_for_type(self, vehicle_type: str) -> str:
        """Get appropriate model name for vehicle type."""
        models = {
            "delivery_van": ["Transit", "Sprinter", "ProMaster", "Express"],
            "box_truck": ["E-450", "M2 106", "4300", "NRR"],
            "semi_trailer": ["579", "T680", "Cascadia", "LT"],
            "cargo_van": ["Transit Connect", "Metris", "City Express"],
        }
        return random.choice(models.get(vehicle_type, ["Standard"]))

    def _generate_license_plate(self) -> str:
        """Generate a fake license plate."""
        letters = "".join(random.choices("ABCDEFGHIJKLMNOPQRSTUVWXYZ", k=3))
        numbers = "".join(random.choices("0123456789", k=4))
        return f"{letters}-{numbers}"

    def _generate_vin(self) -> str:
        """Generate a fake VIN (Vehicle Identification Number)."""
        chars = "0123456789ABCDEFGHJKLMNPRSTUVWXYZ"
        return "".join(random.choices(chars, k=17))
