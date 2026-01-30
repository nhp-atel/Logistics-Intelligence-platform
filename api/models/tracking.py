"""Tracking models."""

from datetime import datetime

from pydantic import BaseModel, Field


class TrackingEventResponse(BaseModel):
    """Tracking event response model."""

    event_id: str = Field(..., description="Unique event identifier")
    package_id: str = Field(..., description="Package identifier")
    event_type: str = Field(..., description="Type of tracking event")
    event_timestamp: datetime = Field(..., description="When the event occurred")
    location_id: str | None = Field(None, description="Location ID")
    location_city: str | None = Field(None, description="City name")
    location_state: str | None = Field(None, description="State code")
    driver_id: str | None = Field(None, description="Driver ID if applicable")
    notes: str | None = Field(None, description="Event notes")
    latitude: float | None = Field(None, description="Latitude")
    longitude: float | None = Field(None, description="Longitude")

    class Config:
        from_attributes = True


class TrackingHistoryResponse(BaseModel):
    """Tracking history response model."""

    package_id: str = Field(..., description="Package identifier")
    events: list[TrackingEventResponse] = Field(..., description="List of tracking events")
    total_events: int = Field(..., description="Total number of events")
