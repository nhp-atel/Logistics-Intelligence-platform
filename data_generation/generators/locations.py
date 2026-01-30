"""Location data generator."""

import random
from typing import Any

from faker import Faker

from data_generation.config import (
    LOCATION_TYPES,
    MAJOR_CITIES,
    STATE_TO_REGION,
    US_STATES,
    GenerationConfig,
)


class LocationGenerator:
    """Generate synthetic location data."""

    def __init__(self, config: GenerationConfig):
        self.config = config
        self.fake = Faker()
        Faker.seed(config.random_seed)
        random.seed(config.random_seed)
        self._hub_locations: list[dict[str, Any]] = []

    def generate(self) -> list[dict[str, Any]]:
        """Generate location records."""
        locations = []

        # First, create hub locations in major cities
        hub_id = 1
        for state, cities in MAJOR_CITIES.items():
            for city_name, lat, lon in cities:
                location = {
                    "location_id": f"LOC{hub_id:08d}",
                    "location_type": "hub" if hub_id <= 10 else "distribution_center",
                    "name": f"{city_name} {('Main Hub' if hub_id <= 10 else 'Distribution Center')}",
                    "address": f"{random.randint(100, 9999)} Logistics Way",
                    "city": city_name,
                    "state": state,
                    "zip_code": self._generate_zip_for_state(state),
                    "country": "US",
                    "latitude": lat + random.uniform(-0.1, 0.1),
                    "longitude": lon + random.uniform(-0.1, 0.1),
                    "timezone": self._get_timezone(state),
                    "region": STATE_TO_REGION.get(state, "unknown"),
                    "is_active": True,
                }
                locations.append(location)
                self._hub_locations.append(location)
                hub_id += 1

        # Generate remaining locations (customer addresses, pickup points)
        for i in range(len(locations), self.config.num_locations):
            location = self._generate_customer_location(i + 1)
            locations.append(location)

        return locations

    def _generate_customer_location(self, index: int) -> dict[str, Any]:
        """Generate a customer address or pickup point location."""
        state = random.choices(
            list(US_STATES.keys()),
            weights=list(US_STATES.values()),
            k=1,
        )[0]

        # Determine location type
        location_type = random.choices(
            ["customer_address", "pickup_point"],
            weights=[0.9, 0.1],
            k=1,
        )[0]

        city = self.fake.city()

        # Generate coordinates near state center (simplified)
        base_lat, base_lon = self._get_state_center(state)
        lat = base_lat + random.uniform(-2.0, 2.0)
        lon = base_lon + random.uniform(-2.0, 2.0)

        return {
            "location_id": f"LOC{index:08d}",
            "location_type": location_type,
            "name": f"{self.fake.street_address()}" if location_type == "customer_address" else f"{city} Pickup Point",
            "address": self.fake.street_address(),
            "city": city,
            "state": state,
            "zip_code": self._generate_zip_for_state(state),
            "country": "US",
            "latitude": round(lat, 6),
            "longitude": round(lon, 6),
            "timezone": self._get_timezone(state),
            "region": STATE_TO_REGION.get(state, "unknown"),
            "is_active": random.random() > 0.02,  # 98% active
        }

    def _generate_zip_for_state(self, state: str) -> str:
        """Generate a plausible ZIP code for a state."""
        # Simplified ZIP code ranges by state
        zip_ranges = {
            "AL": (35000, 36999), "AK": (99500, 99999), "AZ": (85000, 86999),
            "AR": (71600, 72999), "CA": (90000, 96699), "CO": (80000, 81699),
            "CT": (6000, 6999), "DE": (19700, 19999), "FL": (32000, 34999),
            "GA": (30000, 31999), "HI": (96700, 96899), "ID": (83200, 83899),
            "IL": (60000, 62999), "IN": (46000, 47999), "IA": (50000, 52899),
            "KS": (66000, 67999), "KY": (40000, 42799), "LA": (70000, 71499),
            "ME": (3900, 4999), "MD": (20600, 21999), "MA": (1000, 2799),
            "MI": (48000, 49999), "MN": (55000, 56799), "MS": (38600, 39799),
            "MO": (63000, 65899), "MT": (59000, 59999), "NE": (68000, 69399),
            "NV": (88900, 89899), "NH": (3000, 3899), "NJ": (7000, 8999),
            "NM": (87000, 88499), "NY": (10000, 14999), "NC": (27000, 28999),
            "ND": (58000, 58899), "OH": (43000, 45999), "OK": (73000, 74999),
            "OR": (97000, 97999), "PA": (15000, 19699), "RI": (2800, 2999),
            "SC": (29000, 29999), "SD": (57000, 57799), "TN": (37000, 38599),
            "TX": (75000, 79999), "UT": (84000, 84799), "VT": (5000, 5999),
            "VA": (22000, 24699), "WA": (98000, 99499), "WV": (24700, 26899),
            "WI": (53000, 54999), "WY": (82000, 83199),
        }
        zip_min, zip_max = zip_ranges.get(state, (10000, 99999))
        return str(random.randint(zip_min, zip_max)).zfill(5)

    def _get_timezone(self, state: str) -> str:
        """Get timezone for a state."""
        eastern = {"CT", "DE", "FL", "GA", "IN", "KY", "ME", "MD", "MA", "MI",
                   "NH", "NJ", "NY", "NC", "OH", "PA", "RI", "SC", "TN", "VT",
                   "VA", "WV"}
        central = {"AL", "AR", "IL", "IA", "KS", "LA", "MN", "MS", "MO", "NE",
                   "ND", "OK", "SD", "TX", "WI"}
        mountain = {"AZ", "CO", "ID", "MT", "NM", "UT", "WY"}
        pacific = {"CA", "NV", "OR", "WA"}

        if state in eastern:
            return "America/New_York"
        elif state in central:
            return "America/Chicago"
        elif state in mountain:
            return "America/Denver"
        elif state in pacific:
            return "America/Los_Angeles"
        elif state == "AK":
            return "America/Anchorage"
        elif state == "HI":
            return "Pacific/Honolulu"
        else:
            return "America/New_York"

    def _get_state_center(self, state: str) -> tuple[float, float]:
        """Get approximate center coordinates for a state."""
        state_centers = {
            "AL": (32.8, -86.8), "AK": (64.0, -153.0), "AZ": (34.2, -111.6),
            "AR": (34.9, -92.4), "CA": (37.2, -119.4), "CO": (39.0, -105.5),
            "CT": (41.6, -72.7), "DE": (39.0, -75.5), "FL": (28.6, -82.4),
            "GA": (32.6, -83.4), "HI": (20.8, -156.3), "ID": (44.4, -114.6),
            "IL": (40.0, -89.2), "IN": (39.9, -86.3), "IA": (42.0, -93.5),
            "KS": (38.5, -98.4), "KY": (37.8, -85.3), "LA": (31.0, -92.0),
            "ME": (45.4, -69.2), "MD": (39.0, -76.8), "MA": (42.2, -71.5),
            "MI": (44.2, -85.4), "MN": (46.3, -94.3), "MS": (32.7, -89.7),
            "MO": (38.4, -92.5), "MT": (47.0, -109.6), "NE": (41.5, -99.8),
            "NV": (39.3, -116.6), "NH": (43.7, -71.6), "NJ": (40.2, -74.7),
            "NM": (34.4, -106.1), "NY": (42.9, -75.5), "NC": (35.5, -79.8),
            "ND": (47.4, -100.5), "OH": (40.4, -82.8), "OK": (35.6, -97.5),
            "OR": (44.0, -120.5), "PA": (40.9, -77.8), "RI": (41.7, -71.5),
            "SC": (33.9, -80.9), "SD": (44.4, -100.2), "TN": (35.8, -86.3),
            "TX": (31.5, -99.4), "UT": (39.3, -111.7), "VT": (44.0, -72.7),
            "VA": (37.5, -78.8), "WA": (47.4, -120.5), "WV": (38.9, -80.5),
            "WI": (44.6, -89.7), "WY": (43.0, -107.5),
        }
        return state_centers.get(state, (39.8, -98.6))

    def get_hub_locations(self) -> list[dict[str, Any]]:
        """Return list of hub/distribution center locations."""
        return self._hub_locations
