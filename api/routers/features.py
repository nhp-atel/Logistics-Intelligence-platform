"""Feature endpoints."""

from fastapi import APIRouter, Depends, HTTPException, Security
from fastapi.security import APIKeyHeader

from api.config import Settings, get_settings
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


@router.get("/features/customer/{customer_id}")
async def get_customer_features(
    customer_id: str,
    api_key: str = Depends(verify_api_key),
    settings: Settings = Depends(get_settings),
) -> dict:
    """Get ML features for a customer."""
    service = BigQueryService(settings)
    features = await service.get_customer_features(customer_id)

    if not features:
        raise HTTPException(
            status_code=404,
            detail=f"Features not found for customer {customer_id}",
        )

    return features


@router.get("/features/route")
async def get_route_features(
    origin_region: str,
    destination_region: str,
    service_type: str,
    api_key: str = Depends(verify_api_key),
    settings: Settings = Depends(get_settings),
) -> dict:
    """Get ML features for a route."""
    service = BigQueryService(settings)
    features = await service.get_route_features(
        origin_region, destination_region, service_type
    )

    if not features:
        raise HTTPException(
            status_code=404,
            detail=f"Features not found for route {origin_region} -> {destination_region}",
        )

    return features


@router.get("/features/delivery/{package_id}")
async def get_delivery_features(
    package_id: str,
    api_key: str = Depends(verify_api_key),
    settings: Settings = Depends(get_settings),
) -> dict:
    """Get ML features for delivery prediction."""
    service = BigQueryService(settings)
    features = await service.get_delivery_features(package_id)

    if not features:
        raise HTTPException(
            status_code=404,
            detail=f"Features not found for package {package_id}",
        )

    return features
