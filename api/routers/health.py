"""Health check endpoints."""

from datetime import datetime

from fastapi import APIRouter, Depends

from api.config import Settings, get_settings

router = APIRouter()


@router.get("/health")
async def health_check(settings: Settings = Depends(get_settings)) -> dict:
    """Health check endpoint."""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "version": settings.app_version,
    }


@router.get("/health/ready")
async def readiness_check() -> dict:
    """Readiness check endpoint."""
    # Could add database connectivity check here
    return {
        "status": "ready",
        "timestamp": datetime.utcnow().isoformat(),
    }


@router.get("/health/live")
async def liveness_check() -> dict:
    """Liveness check endpoint."""
    return {
        "status": "alive",
        "timestamp": datetime.utcnow().isoformat(),
    }
