"""Configuration for data generation."""

from datetime import datetime
from pathlib import Path
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings


class GenerationConfig(BaseSettings):
    """Configuration for synthetic data generation."""

    # Output settings
    output_dir: Path = Field(default=Path("data/generated"))
    output_format: Literal["csv", "parquet", "json"] = "parquet"

    # Volume settings
    num_packages: int = Field(default=10000, ge=100, le=1000000)
    num_customers: int = Field(default=5000, ge=50, le=100000)
    num_drivers: int = Field(default=500, ge=10, le=10000)
    num_vehicles: int = Field(default=300, ge=10, le=5000)
    num_locations: int = Field(default=1000, ge=50, le=50000)

    # Time range
    start_date: datetime = Field(default_factory=lambda: datetime(2023, 1, 1))
    end_date: datetime = Field(default_factory=lambda: datetime(2024, 12, 31))

    # Distribution settings
    business_customer_pct: float = Field(default=0.3, ge=0.0, le=1.0)
    express_service_pct: float = Field(default=0.15, ge=0.0, le=1.0)
    next_day_service_pct: float = Field(default=0.10, ge=0.0, le=1.0)
    exception_rate: float = Field(default=0.05, ge=0.0, le=0.5)
    late_delivery_rate: float = Field(default=0.08, ge=0.0, le=0.5)

    # Realistic patterns
    weekday_volume_boost: float = Field(default=1.3, ge=1.0, le=2.0)
    holiday_volume_boost: float = Field(default=1.8, ge=1.0, le=3.0)
    q4_volume_boost: float = Field(default=1.5, ge=1.0, le=2.5)

    # Random seed for reproducibility
    random_seed: int = Field(default=42)

    # GCS settings for upload
    gcs_bucket: str | None = None
    gcs_prefix: str = "raw"

    class Config:
        env_prefix = "DATA_GEN_"


# US States with population weights for realistic distribution
US_STATES = {
    "CA": 0.12,
    "TX": 0.09,
    "FL": 0.07,
    "NY": 0.06,
    "PA": 0.04,
    "IL": 0.04,
    "OH": 0.04,
    "GA": 0.03,
    "NC": 0.03,
    "MI": 0.03,
    "NJ": 0.03,
    "VA": 0.03,
    "WA": 0.02,
    "AZ": 0.02,
    "MA": 0.02,
    "TN": 0.02,
    "IN": 0.02,
    "MO": 0.02,
    "MD": 0.02,
    "WI": 0.02,
    "CO": 0.02,
    "MN": 0.02,
    "SC": 0.02,
    "AL": 0.02,
    "LA": 0.01,
    "KY": 0.01,
    "OR": 0.01,
    "OK": 0.01,
    "CT": 0.01,
    "UT": 0.01,
    "NV": 0.01,
    "AR": 0.01,
    "MS": 0.01,
    "KS": 0.01,
    "NM": 0.01,
    "NE": 0.01,
    "ID": 0.01,
    "WV": 0.01,
    "HI": 0.005,
    "NH": 0.005,
    "ME": 0.005,
    "RI": 0.005,
    "MT": 0.003,
    "DE": 0.003,
    "SD": 0.003,
    "ND": 0.002,
    "AK": 0.002,
    "VT": 0.002,
    "WY": 0.002,
}

# Service types with base transit times
SERVICE_TYPES = {
    "ground": {"base_days": 5, "cost_multiplier": 1.0},
    "express": {"base_days": 2, "cost_multiplier": 2.5},
    "next_day": {"base_days": 1, "cost_multiplier": 4.0},
    "freight": {"base_days": 7, "cost_multiplier": 0.8},
}

# Event types in order
EVENT_TYPES = [
    "order_placed",
    "label_created",
    "picked_up",
    "arrived_at_origin_hub",
    "departed_origin_hub",
    "in_transit",
    "arrived_at_destination_hub",
    "out_for_delivery",
    "delivered",
]

EXCEPTION_EVENTS = [
    "weather_delay",
    "address_issue",
    "recipient_unavailable",
    "customs_hold",
    "mechanical_issue",
    "rerouted",
]

# Customer tiers
CUSTOMER_TIERS = {
    "bronze": {"min_orders": 0, "discount": 0.0},
    "silver": {"min_orders": 10, "discount": 0.05},
    "gold": {"min_orders": 50, "discount": 0.10},
    "platinum": {"min_orders": 200, "discount": 0.15},
}

# Location types
LOCATION_TYPES = [
    "hub",
    "distribution_center",
    "pickup_point",
    "customer_address",
    "airport",
    "ground_hub",
]

# Regions mapping
STATE_TO_REGION = {
    "CT": "northeast",
    "ME": "northeast",
    "MA": "northeast",
    "NH": "northeast",
    "RI": "northeast",
    "VT": "northeast",
    "NJ": "northeast",
    "NY": "northeast",
    "PA": "northeast",
    "IL": "midwest",
    "IN": "midwest",
    "MI": "midwest",
    "OH": "midwest",
    "WI": "midwest",
    "IA": "midwest",
    "KS": "midwest",
    "MN": "midwest",
    "MO": "midwest",
    "NE": "midwest",
    "ND": "midwest",
    "SD": "midwest",
    "DE": "south",
    "FL": "south",
    "GA": "south",
    "MD": "south",
    "NC": "south",
    "SC": "south",
    "VA": "south",
    "WV": "south",
    "AL": "south",
    "KY": "south",
    "MS": "south",
    "TN": "south",
    "AR": "south",
    "LA": "south",
    "OK": "south",
    "TX": "south",
    "AZ": "west",
    "CO": "west",
    "ID": "west",
    "MT": "west",
    "NV": "west",
    "NM": "west",
    "UT": "west",
    "WY": "west",
    "AK": "west",
    "CA": "west",
    "HI": "west",
    "OR": "west",
    "WA": "west",
}

# Major cities for hub locations
MAJOR_CITIES = {
    "CA": [
        ("Los Angeles", 34.0522, -118.2437),
        ("San Francisco", 37.7749, -122.4194),
        ("San Diego", 32.7157, -117.1611),
    ],
    "TX": [
        ("Houston", 29.7604, -95.3698),
        ("Dallas", 32.7767, -96.7970),
        ("Austin", 30.2672, -97.7431),
    ],
    "NY": [
        ("New York", 40.7128, -74.0060),
        ("Buffalo", 42.8864, -78.8784),
    ],
    "FL": [
        ("Miami", 25.7617, -80.1918),
        ("Orlando", 28.5383, -81.3792),
        ("Tampa", 27.9506, -82.4572),
    ],
    "IL": [("Chicago", 41.8781, -87.6298)],
    "PA": [
        ("Philadelphia", 39.9526, -75.1652),
        ("Pittsburgh", 40.4406, -79.9959),
    ],
    "OH": [
        ("Columbus", 39.9612, -82.9988),
        ("Cleveland", 41.4993, -81.6944),
    ],
    "GA": [("Atlanta", 33.7490, -84.3880)],
    "WA": [("Seattle", 47.6062, -122.3321)],
    "AZ": [("Phoenix", 33.4484, -112.0740)],
    "MA": [("Boston", 42.3601, -71.0589)],
    "CO": [("Denver", 39.7392, -104.9903)],
    "TN": [("Nashville", 36.1627, -86.7816)],
    "NV": [("Las Vegas", 36.1699, -115.1398)],
    "OR": [("Portland", 45.5152, -122.6784)],
    "MO": [
        ("Kansas City", 39.0997, -94.5786),
        ("St. Louis", 38.6270, -90.1994),
    ],
    "KY": [("Louisville", 38.2527, -85.7585)],
    "IN": [("Indianapolis", 39.7684, -86.1581)],
    "NC": [("Charlotte", 35.2271, -80.8431)],
    "NJ": [("Newark", 40.7357, -74.1724)],
    "MI": [("Detroit", 42.3314, -83.0458)],
    "MN": [("Minneapolis", 44.9778, -93.2650)],
}

# US Holidays (simplified)
US_HOLIDAYS_2024 = [
    datetime(2024, 1, 1),  # New Year's Day
    datetime(2024, 1, 15),  # MLK Day
    datetime(2024, 2, 19),  # Presidents Day
    datetime(2024, 5, 27),  # Memorial Day
    datetime(2024, 7, 4),  # Independence Day
    datetime(2024, 9, 2),  # Labor Day
    datetime(2024, 10, 14),  # Columbus Day
    datetime(2024, 11, 11),  # Veterans Day
    datetime(2024, 11, 28),  # Thanksgiving
    datetime(2024, 12, 25),  # Christmas
]
