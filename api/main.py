"""FastAPI application entry point."""

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from api.config import get_settings
from api.routers import deliveries, features, health, tracking

settings = get_settings()


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan events."""
    # Startup
    print(f"Starting {settings.app_name} v{settings.app_version}")
    yield
    # Shutdown
    print("Shutting down...")


app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="""
    Logistics Data Platform API provides access to delivery analytics,
    tracking information, and ML features for the logistics platform.

    ## Features

    * **Deliveries** - Query delivery information by package ID or filters
    * **Tracking** - Get tracking events for packages
    * **Features** - Access ML features for predictions
    * **Analytics** - Aggregate statistics and metrics

    ## Authentication

    All endpoints require an API key passed in the `X-API-Key` header.
    """,
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Exception handlers
@app.exception_handler(Exception)
async def global_exception_handler(_request: Request, exc: Exception) -> JSONResponse:
    """Handle uncaught exceptions."""
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error", "type": type(exc).__name__},
    )


# Include routers
app.include_router(health.router, tags=["Health"])
app.include_router(deliveries.router, prefix="/api/v1", tags=["Deliveries"])
app.include_router(tracking.router, prefix="/api/v1", tags=["Tracking"])
app.include_router(features.router, prefix="/api/v1", tags=["Features"])


@app.get("/")
async def root() -> dict:
    """Root endpoint."""
    return {
        "name": settings.app_name,
        "version": settings.app_version,
        "docs": "/docs",
    }
