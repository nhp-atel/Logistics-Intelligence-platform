"""Package/shipment data generator."""

import random
from datetime import datetime, timedelta
from typing import Any

from faker import Faker

from data_generation.config import (
    SERVICE_TYPES,
    US_HOLIDAYS_2024,
    GenerationConfig,
)


class PackageGenerator:
    """Generate synthetic package/shipment data."""

    def __init__(
        self,
        config: GenerationConfig,
        customer_ids: list[str],
        location_ids: list[str],
        hub_location_ids: list[str],
    ):
        self.config = config
        self.customer_ids = customer_ids
        self.location_ids = location_ids
        self.hub_location_ids = hub_location_ids
        self.fake = Faker()
        Faker.seed(config.random_seed)
        random.seed(config.random_seed)

    def generate(self) -> list[dict[str, Any]]:
        """Generate package records."""
        packages = []

        # Distribute packages across the date range with realistic patterns
        date_weights = self._calculate_date_weights()
        total_weight = sum(date_weights.values())
        normalized_weights = {d: w / total_weight for d, w in date_weights.items()}

        # Assign package counts to each day
        dates = list(normalized_weights.keys())
        weights = list(normalized_weights.values())

        for i in range(self.config.num_packages):
            package_id = f"PKG{i + 1:012d}"

            # Select date based on weights
            created_date = random.choices(dates, weights=weights, k=1)[0]

            package = self._generate_package(package_id, created_date, i)
            packages.append(package)

        return packages

    def _calculate_date_weights(self) -> dict[datetime, float]:
        """Calculate weights for each date based on realistic patterns."""
        weights = {}
        current = self.config.start_date

        while current <= self.config.end_date:
            weight = 1.0

            # Day of week pattern (higher Mon-Fri)
            if current.weekday() < 5:  # Weekday
                weight *= self.config.weekday_volume_boost
            else:  # Weekend
                weight *= 0.6

            # Q4 boost (Oct-Dec)
            if current.month >= 10:
                weight *= self.config.q4_volume_boost

            # Holiday period boost (around major holidays)
            for holiday in US_HOLIDAYS_2024:
                if holiday.year == current.year:
                    days_to_holiday = abs((current - holiday).days)
                    if days_to_holiday <= 7:
                        weight *= self.config.holiday_volume_boost * (1 - days_to_holiday / 14)

            # Black Friday / Cyber Monday boost
            if current.month == 11 and current.day >= 25 and current.day <= 30:
                weight *= 2.0

            weights[current] = weight
            current += timedelta(days=1)

        return weights

    def _generate_package(
        self, package_id: str, created_date: datetime, _index: int
    ) -> dict[str, Any]:
        """Generate a single package record."""
        # Select sender and recipient (different customers)
        sender_id = random.choice(self.customer_ids)
        recipient_id = random.choice([c for c in self.customer_ids if c != sender_id])

        # Select origin and destination locations
        origin_id = random.choice(self.location_ids)
        destination_id = random.choice([loc for loc in self.location_ids if loc != origin_id])

        # Determine service type
        service_type = self._select_service_type()

        # Generate package dimensions
        weight_lbs = self._generate_weight()
        dimensions = self._generate_dimensions()

        # Calculate estimated delivery based on service type
        base_days = SERVICE_TYPES[service_type]["base_days"]
        # Add variability
        transit_days = base_days + random.randint(0, 2)
        estimated_delivery = created_date + timedelta(days=transit_days)

        # Determine if delivered and when
        status, actual_delivery = self._determine_delivery_status(
            created_date, estimated_delivery
        )

        # Calculate cost
        cost = self._calculate_shipping_cost(weight_lbs, service_type, dimensions)

        # Generate tracking number
        tracking_number = self._generate_tracking_number()

        return {
            "package_id": package_id,
            "tracking_number": tracking_number,
            "sender_customer_id": sender_id,
            "recipient_customer_id": recipient_id,
            "origin_location_id": origin_id,
            "destination_location_id": destination_id,
            "weight_lbs": round(weight_lbs, 2),
            "length_in": dimensions["length"],
            "width_in": dimensions["width"],
            "height_in": dimensions["height"],
            "volume_cubic_in": dimensions["length"] * dimensions["width"] * dimensions["height"],
            "service_type": service_type,
            "created_at": created_date.isoformat(),
            "estimated_delivery_date": estimated_delivery.date().isoformat(),
            "actual_delivery_date": actual_delivery.date().isoformat() if actual_delivery else None,
            "status": status,
            "shipping_cost": round(cost, 2),
            "declared_value": round(random.uniform(10, 500), 2) if random.random() > 0.7 else None,
            "signature_required": random.random() < 0.3,
            "is_fragile": random.random() < 0.15,
            "is_hazardous": random.random() < 0.02,
            "special_instructions": self._generate_special_instructions() if random.random() < 0.1 else None,
        }

    def _select_service_type(self) -> str:
        """Select service type based on configuration."""
        roll = random.random()

        if roll < self.config.next_day_service_pct:
            return "next_day"
        elif roll < self.config.next_day_service_pct + self.config.express_service_pct:
            return "express"
        elif roll < 0.95:
            return "ground"
        else:
            return "freight"

    def _generate_weight(self) -> float:
        """Generate realistic package weight."""
        # Most packages are light, some are heavy
        weight_type = random.choices(
            ["light", "medium", "heavy", "freight"],
            weights=[0.5, 0.35, 0.12, 0.03],
            k=1,
        )[0]

        if weight_type == "light":
            return random.uniform(0.5, 5)
        elif weight_type == "medium":
            return random.uniform(5, 20)
        elif weight_type == "heavy":
            return random.uniform(20, 70)
        else:
            return random.uniform(70, 500)

    def _generate_dimensions(self) -> dict[str, float]:
        """Generate package dimensions."""
        # Standard box sizes
        sizes = [
            {"length": 6, "width": 4, "height": 4},
            {"length": 8, "width": 6, "height": 4},
            {"length": 10, "width": 8, "height": 6},
            {"length": 12, "width": 10, "height": 8},
            {"length": 14, "width": 12, "height": 10},
            {"length": 18, "width": 14, "height": 12},
            {"length": 24, "width": 18, "height": 16},
            {"length": 36, "width": 24, "height": 24},
        ]

        base = random.choice(sizes)

        # Add some variation
        return {
            "length": round(base["length"] * random.uniform(0.9, 1.1), 1),
            "width": round(base["width"] * random.uniform(0.9, 1.1), 1),
            "height": round(base["height"] * random.uniform(0.9, 1.1), 1),
        }

    def _determine_delivery_status(
        self, created_date: datetime, estimated_delivery: datetime
    ) -> tuple[str, datetime | None]:
        """Determine package delivery status and actual delivery date."""
        now = self.config.end_date

        # If created recently, might still be in transit
        if created_date > now - timedelta(days=7):
            status_roll = random.random()
            if status_roll < 0.3:
                return "in_transit", None
            elif status_roll < 0.4:
                return "out_for_delivery", None

        # Most packages are delivered
        if random.random() > self.config.exception_rate:
            # Determine if on time
            if random.random() > self.config.late_delivery_rate:
                # On time
                days_variance = random.randint(-1, 0)
            else:
                # Late
                days_variance = random.randint(1, 5)

            actual_delivery = estimated_delivery + timedelta(days=days_variance)
            return "delivered", actual_delivery
        else:
            # Exception occurred
            exception_type = random.choice([
                "exception",
                "returned",
                "lost",
            ])
            return exception_type, None

    def _calculate_shipping_cost(
        self, weight: float, service_type: str, dimensions: dict
    ) -> float:
        """Calculate shipping cost based on weight and service type."""
        base_rate = 5.0

        # Weight-based cost
        if weight <= 1:
            weight_cost = 3.0
        elif weight <= 5:
            weight_cost = 5.0
        elif weight <= 20:
            weight_cost = 8.0 + (weight - 5) * 0.5
        else:
            weight_cost = 15.0 + (weight - 20) * 0.3

        # Dimensional weight (industry standard: divide by 139)
        dim_weight = (
            dimensions["length"] * dimensions["width"] * dimensions["height"]
        ) / 139
        billable_weight = max(weight, dim_weight)

        # Apply service multiplier
        multiplier = SERVICE_TYPES[service_type]["cost_multiplier"]

        return float((base_rate + weight_cost * (billable_weight / weight)) * multiplier)

    def _generate_tracking_number(self) -> str:
        """Generate a realistic tracking number."""
        prefix = random.choice(["1Z", "94", "92", "93"])
        if prefix == "1Z":
            # UPS-style
            chars = "".join(random.choices("0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ", k=16))
            return f"{prefix}{chars}"
        else:
            # USPS-style
            nums = "".join(random.choices("0123456789", k=20))
            return f"{prefix}{nums}"

    def _generate_special_instructions(self) -> str:
        """Generate special delivery instructions."""
        instructions = [
            "Leave at front door",
            "Leave at back door",
            "Leave with neighbor",
            "Ring doorbell twice",
            "Do not bend",
            "Keep upright",
            "Fragile - handle with care",
            "Leave in garage",
            "Call before delivery",
            "Deliver to leasing office",
        ]
        return random.choice(instructions)
