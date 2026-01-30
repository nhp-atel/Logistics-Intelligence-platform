"""Delivery endpoints."""

from datetime import date
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, Security
from fastapi.security import APIKeyHeader

from api.config import Settings, get_settings
from api.models.delivery import DeliveryResponse, DeliveryListResponse, DeliverySummary
from api.services.bigquery_service import BigQueryService

router = APIRouter()
api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


async def verify_api_key(
    api_key: str = Security(api_key_header),
    settings: Settings = Depends(get_settings),
) -> str:
    """Verify API key."""
    if not api_key or api_key != settings.api_key:
        if settings.debug:
            return "debug"
        raise HTTPException(status_code=401, detail="Invalid or missing API key")
    return api_key


@router.get("/deliveries/{package_id}", response_model=DeliveryResponse)
async def get_delivery(
    package_id: str,
    api_key: str = Depends(verify_api_key),
    settings: Settings = Depends(get_settings),
) -> DeliveryResponse:
    """Get delivery information by package ID."""
    service = BigQueryService(settings)
    delivery = await service.get_delivery(package_id)

    if not delivery:
        raise HTTPException(status_code=404, detail=f"Package {package_id} not found")

    return DeliveryResponse(**delivery)


@router.get("/deliveries", response_model=DeliveryListResponse)
async def list_deliveries(
    status: Annotated[str | None, Query(description="Filter by status")] = None,
    service_type: Annotated[str | None, Query(description="Filter by service type")] = None,
    origin_state: Annotated[str | None, Query(description="Filter by origin state")] = None,
    destination_state: Annotated[str | None, Query(description="Filter by destination state")] = None,
    start_date: Annotated[date | None, Query(description="Start date for created_at")] = None,
    end_date: Annotated[date | None, Query(description="End date for created_at")] = None,
    limit: Annotated[int, Query(ge=1, le=1000, description="Maximum results")] = 100,
    offset: Annotated[int, Query(ge=0, description="Offset for pagination")] = 0,
    api_key: str = Depends(verify_api_key),
    settings: Settings = Depends(get_settings),
) -> DeliveryListResponse:
    """List deliveries with optional filters."""
    service = BigQueryService(settings)
    deliveries, total = await service.list_deliveries(
        status=status,
        service_type=service_type,
        origin_state=origin_state,
        destination_state=destination_state,
        start_date=start_date,
        end_date=end_date,
        limit=limit,
        offset=offset,
    )

    return DeliveryListResponse(
        items=[DeliveryResponse(**d) for d in deliveries],
        total=total,
        limit=limit,
        offset=offset,
    )


@router.get("/analytics/summary", response_model=DeliverySummary)
async def get_delivery_summary(
    start_date: Annotated[date | None, Query(description="Start date")] = None,
    end_date: Annotated[date | None, Query(description="End date")] = None,
    api_key: str = Depends(verify_api_key),
    settings: Settings = Depends(get_settings),
) -> DeliverySummary:
    """Get aggregate delivery statistics."""
    service = BigQueryService(settings)
    summary = await service.get_delivery_summary(start_date, end_date)
    return DeliverySummary(**summary)
