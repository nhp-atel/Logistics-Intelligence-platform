"""Tracking event data generator."""

import random
from datetime import datetime, timedelta
from typing import Any

from faker import Faker

from data_generation.config import (
    EVENT_TYPES,
    EXCEPTION_EVENTS,
    GenerationConfig,
)


class TrackingEventGenerator:
    """Generate synthetic tracking event data."""

    def __init__(
        self,
        config: GenerationConfig,
        packages: list[dict[str, Any]],
        locations: list[dict[str, Any]],
        hub_location_ids: list[str],
        driver_ids: list[str],
        vehicle_ids: list[str],
    ):
        self.config = config
        self.packages = packages
        self.locations = locations
        self.hub_location_ids = hub_location_ids
        self.driver_ids = driver_ids
        self.vehicle_ids = vehicle_ids
        self.fake = Faker()
        Faker.seed(config.random_seed)
        random.seed(config.random_seed)

        # Build location lookup
        self.location_lookup = {loc["location_id"]: loc for loc in locations}

    def generate(self) -> list[dict[str, Any]]:
        """Generate tracking event records."""
        events = []
        event_counter = 0

        for package in self.packages:
            package_events = self._generate_package_events(package, event_counter)
            events.extend(package_events)
            event_counter += len(package_events)

        # Sort by timestamp
        events.sort(key=lambda x: x["event_timestamp"])

        return events

    def _generate_package_events(
        self, package: dict[str, Any], start_id: int
    ) -> list[dict[str, Any]]:
        """Generate all tracking events for a single package."""
        events = []
        event_id = start_id

        created_at = datetime.fromisoformat(package["created_at"])
        status = package["status"]

        # Determine how many events to generate based on status
        if status == "delivered":
            # Full event sequence
            event_sequence = EVENT_TYPES.copy()
        elif status == "in_transit":
            # Partial sequence
            num_events = random.randint(4, 6)
            event_sequence = EVENT_TYPES[:num_events]
        elif status == "out_for_delivery":
            event_sequence = EVENT_TYPES[:-1]  # All except delivered
        elif status == "exception":
            num_events = random.randint(3, 6)
            event_sequence = EVENT_TYPES[:num_events]
            # Add exception event
            event_sequence.append(random.choice(EXCEPTION_EVENTS))
        elif status == "returned":
            num_events = random.randint(4, 7)
            event_sequence = EVENT_TYPES[:num_events]
            event_sequence.extend(["return_initiated", "returned_to_sender"])
        else:
            event_sequence = EVENT_TYPES[:3]  # Minimal events

        current_time = created_at
        previous_location_id = package["origin_location_id"]

        for i, event_type in enumerate(event_sequence):
            event_id += 1

            # Calculate time for this event
            time_delta = self._calculate_event_time_delta(event_type, i)
            current_time = current_time + time_delta

            # Determine location for this event
            location_id = self._determine_event_location(
                event_type, package, previous_location_id
            )

            # Assign driver and vehicle for appropriate events
            driver_id = None
            vehicle_id = None
            if event_type in ["picked_up", "out_for_delivery", "delivered"]:
                driver_id = random.choice(self.driver_ids) if self.driver_ids else None
                vehicle_id = random.choice(self.vehicle_ids) if self.vehicle_ids else None

            event = {
                "event_id": f"EVT{event_id:012d}",
                "package_id": package["package_id"],
                "location_id": location_id,
                "event_type": event_type,
                "event_timestamp": current_time.isoformat(),
                "driver_id": driver_id,
                "vehicle_id": vehicle_id,
                "notes": self._generate_event_notes(event_type),
                "latitude": self._get_location_lat(location_id),
                "longitude": self._get_location_lon(location_id),
            }
            events.append(event)

            previous_location_id = location_id

        return events

    def _calculate_event_time_delta(self, event_type: str, event_index: int) -> timedelta:
        """Calculate time between events."""
        base_hours = {
            "order_placed": 0,
            "label_created": random.uniform(0.5, 4),
            "picked_up": random.uniform(2, 24),
            "arrived_at_origin_hub": random.uniform(1, 6),
            "departed_origin_hub": random.uniform(2, 8),
            "in_transit": random.uniform(12, 48),
            "arrived_at_destination_hub": random.uniform(6, 24),
            "out_for_delivery": random.uniform(6, 14),
            "delivered": random.uniform(1, 8),
            # Exception events
            "weather_delay": random.uniform(4, 24),
            "address_issue": random.uniform(0.5, 2),
            "recipient_unavailable": random.uniform(0.5, 4),
            "customs_hold": random.uniform(24, 72),
            "mechanical_issue": random.uniform(2, 12),
            "rerouted": random.uniform(2, 8),
            "return_initiated": random.uniform(4, 24),
            "returned_to_sender": random.uniform(24, 96),
        }

        hours = base_hours.get(event_type, random.uniform(1, 12))
        return timedelta(hours=hours)

    def _determine_event_location(
        self,
        event_type: str,
        package: dict[str, Any],
        previous_location_id: str,
    ) -> str:
        """Determine the location for an event."""
        if event_type in ["order_placed", "label_created"]:
            return package["origin_location_id"]

        if event_type == "picked_up":
            return package["origin_location_id"]

        if event_type in ["arrived_at_origin_hub", "departed_origin_hub"]:
            # Select a hub near origin
            return random.choice(self.hub_location_ids) if self.hub_location_ids else package["origin_location_id"]

        if event_type == "in_transit":
            # Could be at any hub
            return random.choice(self.hub_location_ids) if self.hub_location_ids else previous_location_id

        if event_type == "arrived_at_destination_hub":
            # Select a hub near destination
            return random.choice(self.hub_location_ids) if self.hub_location_ids else package["destination_location_id"]

        if event_type in ["out_for_delivery", "delivered"]:
            return package["destination_location_id"]

        if event_type in EXCEPTION_EVENTS:
            return previous_location_id

        if event_type in ["return_initiated", "returned_to_sender"]:
            return previous_location_id

        return previous_location_id

    def _generate_event_notes(self, event_type: str) -> str | None:
        """Generate notes for certain event types."""
        notes_map = {
            "weather_delay": [
                "Delayed due to severe weather conditions",
                "Winter storm causing delays in area",
                "Heavy rain impacting deliveries",
                "Tornado warning - operations suspended",
            ],
            "address_issue": [
                "Address not found - verifying with sender",
                "Business closed - will reattempt",
                "No access to building",
                "Address incomplete - missing unit number",
            ],
            "recipient_unavailable": [
                "No one available to sign",
                "Delivery attempted - no response",
                "Left delivery notice",
                "Will reattempt next business day",
            ],
            "delivered": [
                "Left at front door",
                "Signed by recipient",
                "Left with neighbor",
                "Left in mailroom",
                "Signed by household member",
                None,
                None,
                None,
            ],
            "out_for_delivery": [
                "With driver for delivery",
                None,
                None,
            ],
        }

        if event_type in notes_map:
            return random.choice(notes_map[event_type])
        return None

    def _get_location_lat(self, location_id: str) -> float | None:
        """Get latitude for a location."""
        loc = self.location_lookup.get(location_id)
        return loc["latitude"] if loc else None

    def _get_location_lon(self, location_id: str) -> float | None:
        """Get longitude for a location."""
        loc = self.location_lookup.get(location_id)
        return loc["longitude"] if loc else None
