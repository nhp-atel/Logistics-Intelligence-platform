"""Feature store configuration."""

from pydantic_settings import BaseSettings


class FeatureStoreConfig(BaseSettings):
    """Configuration for feature store."""

    # GCP settings
    gcp_project_id: str = ""
    bq_dataset_features: str = "features"

    # Feature computation settings
    default_lookback_days: int = 30
    batch_size: int = 10000

    # Caching
    enable_cache: bool = True
    cache_ttl_seconds: int = 3600

    class Config:
        env_prefix = "FEATURE_STORE_"
