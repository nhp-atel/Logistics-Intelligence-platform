"""API configuration."""

from functools import lru_cache

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings."""

    # App info
    app_name: str = "Logistics Data Platform API"
    app_version: str = "1.0.0"
    debug: bool = False

    # GCP settings
    gcp_project_id: str = ""
    bq_dataset_warehouse: str = "warehouse"
    bq_dataset_features: str = "features"

    # API settings
    api_key: str = ""
    api_host: str = "0.0.0.0"
    api_port: int = 8000

    # Rate limiting
    rate_limit_requests: int = 100
    rate_limit_period: int = 60

    class Config:
        env_file = ".env"
        env_prefix = ""
        case_sensitive = False


@lru_cache
def get_settings() -> Settings:
    """Get cached settings."""
    return Settings()
