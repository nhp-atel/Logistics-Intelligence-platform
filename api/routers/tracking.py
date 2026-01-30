"""Tracking endpoints."""

from fastapi import APIRouter, Depends, HTTPException, Security
from fastapi.security import APIKeyHeader

from api.config import Settings, get_settings
from api.models.tracking import TrackingEventResponse, TrackingHistoryResponse
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


@router.get("/tracking/{package_id}", response_model=TrackingHistoryResponse)
async def get_tracking_history(
    package_id: str,
    api_key: str = Depends(verify_api_key),
    settings: Settings = Depends(get_settings),
) -> TrackingHistoryResponse:
    """Get tracking history for a package."""
    service = BigQueryService(settings)
    events = await service.get_tracking_events(package_id)

    if not events:
        raise HTTPException(
            status_code=404,
            detail=f"No tracking events found for package {package_id}",
        )

    return TrackingHistoryResponse(
        package_id=package_id,
        events=[TrackingEventResponse(**e) for e in events],
        total_events=len(events),
    )


@router.get("/tracking/{package_id}/latest", response_model=TrackingEventResponse)
async def get_latest_tracking_event(
    package_id: str,
    api_key: str = Depends(verify_api_key),
    settings: Settings = Depends(get_settings),
) -> TrackingEventResponse:
    """Get the latest tracking event for a package."""
    service = BigQueryService(settings)
    event = await service.get_latest_tracking_event(package_id)

    if not event:
        raise HTTPException(
            status_code=404,
            detail=f"No tracking events found for package {package_id}",
        )

    return TrackingEventResponse(**event)
