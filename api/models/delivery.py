"""Delivery models."""

from datetime import date, datetime

from pydantic import BaseModel, Field


class DeliveryResponse(BaseModel):
    """Delivery response model."""

    package_id: str = Field(..., description="Unique package identifier")
    tracking_number: str = Field(..., description="Public tracking number")
    sender_customer_id: str | None = Field(None, description="Sender customer ID")
    recipient_customer_id: str | None = Field(None, description="Recipient customer ID")
    origin_location_id: str | None = Field(None, description="Origin location ID")
    destination_location_id: str | None = Field(None, description="Destination location ID")
    origin_state: str | None = Field(None, description="Origin state")
    destination_state: str | None = Field(None, description="Destination state")
    service_type: str = Field(..., description="Service type (GROUND, EXPRESS, etc.)")
    status: str = Field(..., description="Current delivery status")
    weight_lbs: float = Field(..., description="Package weight in pounds")
    volume_cubic_in: float | None = Field(None, description="Package volume")
    shipping_cost: float | None = Field(None, description="Shipping cost")
    created_at: datetime = Field(..., description="When the package was created")
    estimated_delivery_date: date | None = Field(None, description="Estimated delivery date")
    actual_delivery_date: date | None = Field(None, description="Actual delivery date")
    is_on_time: bool | None = Field(None, description="Whether delivered on time")
    transit_days: int | None = Field(None, description="Transit time in days")

    class Config:
        from_attributes = True


class DeliveryListResponse(BaseModel):
    """Paginated delivery list response."""

    items: list[DeliveryResponse]
    total: int
    limit: int
    offset: int


class DeliverySummary(BaseModel):
    """Delivery summary statistics."""

    total_packages: int = Field(..., description="Total number of packages")
    delivered_count: int = Field(..., description="Number of delivered packages")
    in_transit_count: int = Field(..., description="Number of packages in transit")
    on_time_rate: float | None = Field(None, description="On-time delivery rate")
    avg_transit_days: float | None = Field(None, description="Average transit time")
    total_revenue: float | None = Field(None, description="Total shipping revenue")
    avg_weight_lbs: float | None = Field(None, description="Average package weight")

    class Config:
        from_attributes = True
