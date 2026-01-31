"""Feature registry for managing feature definitions."""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class FeatureType(Enum):
    """Types of features."""

    NUMERIC = "numeric"
    CATEGORICAL = "categorical"
    BOOLEAN = "boolean"
    TIMESTAMP = "timestamp"
    ARRAY = "array"


@dataclass
class FeatureDefinition:
    """Definition of a single feature."""

    name: str
    description: str
    feature_type: FeatureType
    entity: str  # e.g., "customer", "package", "route"
    table: str
    column: str
    default_value: Any = None
    tags: list[str] = field(default_factory=list)


class FeatureRegistry:
    """Registry for managing feature definitions."""

    def __init__(self) -> None:
        self._features: dict[str, FeatureDefinition] = {}
        self._register_default_features()

    def _register_default_features(self) -> None:
        """Register default feature definitions."""
        # Customer features
        self.register(
            FeatureDefinition(
                name="customer_total_packages_30d",
                description="Total packages sent by customer in last 30 days",
                feature_type=FeatureType.NUMERIC,
                entity="customer",
                table="ftr_customer_segments",
                column="total_packages_30d",
                default_value=0,
                tags=["customer", "volume", "30d"],
            )
        )

        self.register(
            FeatureDefinition(
                name="customer_total_spend_30d",
                description="Total spending by customer in last 30 days",
                feature_type=FeatureType.NUMERIC,
                entity="customer",
                table="ftr_customer_segments",
                column="total_spend_30d",
                default_value=0.0,
                tags=["customer", "value", "30d"],
            )
        )

        self.register(
            FeatureDefinition(
                name="customer_churn_risk",
                description="Probability of customer churning",
                feature_type=FeatureType.NUMERIC,
                entity="customer",
                table="ftr_customer_segments",
                column="churn_risk_score",
                default_value=0.5,
                tags=["customer", "risk", "ml"],
            )
        )

        self.register(
            FeatureDefinition(
                name="customer_value_score",
                description="RFM-based customer value score (1-3)",
                feature_type=FeatureType.NUMERIC,
                entity="customer",
                table="ftr_customer_segments",
                column="customer_value_score",
                default_value=1.0,
                tags=["customer", "value", "rfm"],
            )
        )

        self.register(
            FeatureDefinition(
                name="customer_segment",
                description="Customer segment label",
                feature_type=FeatureType.CATEGORICAL,
                entity="customer",
                table="ftr_customer_segments",
                column="customer_segment",
                default_value="new",
                tags=["customer", "segment"],
            )
        )

        # Route features
        self.register(
            FeatureDefinition(
                name="route_avg_transit_hours",
                description="Average transit time for route",
                feature_type=FeatureType.NUMERIC,
                entity="route",
                table="ftr_route_performance",
                column="avg_transit_hours",
                default_value=48.0,
                tags=["route", "performance", "time"],
            )
        )

        self.register(
            FeatureDefinition(
                name="route_on_time_rate",
                description="On-time delivery rate for route",
                feature_type=FeatureType.NUMERIC,
                entity="route",
                table="ftr_route_performance",
                column="on_time_rate",
                default_value=0.85,
                tags=["route", "performance", "quality"],
            )
        )

        # Delivery prediction features
        self.register(
            FeatureDefinition(
                name="package_weight_lbs",
                description="Package weight in pounds",
                feature_type=FeatureType.NUMERIC,
                entity="package",
                table="ftr_delivery_predictions",
                column="weight_lbs",
                default_value=5.0,
                tags=["package", "physical"],
            )
        )

        self.register(
            FeatureDefinition(
                name="is_weekend",
                description="Whether package was created on weekend",
                feature_type=FeatureType.BOOLEAN,
                entity="package",
                table="ftr_delivery_predictions",
                column="is_weekend",
                default_value=False,
                tags=["package", "time"],
            )
        )

        self.register(
            FeatureDefinition(
                name="is_peak_season",
                description="Whether package was created during peak season",
                feature_type=FeatureType.BOOLEAN,
                entity="package",
                table="ftr_delivery_predictions",
                column="is_peak_season",
                default_value=False,
                tags=["package", "time", "seasonal"],
            )
        )

    def register(self, feature: FeatureDefinition) -> None:
        """Register a feature definition."""
        self._features[feature.name] = feature

    def get(self, name: str) -> FeatureDefinition | None:
        """Get a feature by name."""
        return self._features.get(name)

    def list_features(self, entity: str | None = None, tags: list[str] | None = None) -> list[FeatureDefinition]:
        """List features, optionally filtered by entity or tags."""
        features = list(self._features.values())

        if entity:
            features = [f for f in features if f.entity == entity]

        if tags:
            features = [f for f in features if any(t in f.tags for t in tags)]

        return features

    def list_entities(self) -> list[str]:
        """List all entities with registered features."""
        return list({f.entity for f in self._features.values()})

    def get_feature_names(self, entity: str) -> list[str]:
        """Get feature names for an entity."""
        return [f.name for f in self._features.values() if f.entity == entity]
