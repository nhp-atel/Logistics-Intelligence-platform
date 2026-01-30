"""Unit tests for data transformations."""

import pytest


def test_service_type_normalization():
    """Test service type normalization logic."""
    raw_values = ["ground", "GROUND", " Ground ", "express", "EXPRESS"]
    expected = ["GROUND", "GROUND", "GROUND", "EXPRESS", "EXPRESS"]

    normalized = [v.strip().upper() for v in raw_values]
    assert normalized == expected


def test_phone_normalization():
    """Test phone number normalization."""
    import re

    raw_phones = [
        "555-123-4567",
        "(555) 123-4567",
        "555.123.4567",
        "5551234567",
    ]
    expected = "5551234567"

    for phone in raw_phones:
        normalized = re.sub(r"[^0-9]", "", phone)
        assert normalized == expected


def test_transit_time_calculation():
    """Test transit time calculation."""
    from datetime import datetime

    created_at = datetime(2024, 6, 15, 10, 0, 0)
    delivered_at = datetime(2024, 6, 18, 14, 0, 0)

    transit_hours = (delivered_at - created_at).total_seconds() / 3600
    transit_days = transit_hours / 24

    assert transit_hours == 76.0
    assert transit_days == pytest.approx(3.167, rel=0.01)


def test_on_time_calculation():
    """Test on-time delivery calculation."""
    from datetime import date

    test_cases = [
        # (actual_date, estimated_date, expected_on_time)
        (date(2024, 6, 18), date(2024, 6, 20), True),   # Early
        (date(2024, 6, 20), date(2024, 6, 20), True),   # On time
        (date(2024, 6, 21), date(2024, 6, 20), False),  # Late
    ]

    for actual, estimated, expected in test_cases:
        is_on_time = actual <= estimated
        assert is_on_time == expected


def test_region_mapping():
    """Test state to region mapping."""
    from data_generation.config import STATE_TO_REGION

    assert STATE_TO_REGION["NY"] == "northeast"
    assert STATE_TO_REGION["CA"] == "west"
    assert STATE_TO_REGION["TX"] == "south"
    assert STATE_TO_REGION["IL"] == "midwest"


def test_customer_value_score():
    """Test customer value score calculation."""
    def calculate_value_score(days_since_order: int, packages_90d: int, spend_90d: float) -> float:
        recency_score = (
            3 if days_since_order <= 30
            else 2 if days_since_order <= 90
            else 1
        )
        frequency_score = (
            3 if packages_90d >= 50
            else 2 if packages_90d >= 10
            else 1
        )
        monetary_score = (
            3 if spend_90d >= 1000
            else 2 if spend_90d >= 200
            else 1
        )
        return (recency_score + frequency_score + monetary_score) / 3.0

    # High value customer
    assert calculate_value_score(10, 60, 2000) == 3.0

    # Low value customer
    assert calculate_value_score(100, 5, 50) == 1.0

    # Medium value customer
    assert calculate_value_score(45, 20, 500) == 2.0


def test_churn_risk_calculation():
    """Test churn risk calculation."""
    def calculate_churn_risk(days_since_order: int | None) -> float:
        if days_since_order is None:
            return 0.9
        if days_since_order > 180:
            return 0.85
        if days_since_order > 90:
            return 0.6
        if days_since_order > 60:
            return 0.4
        if days_since_order > 30:
            return 0.2
        return 0.05

    assert calculate_churn_risk(None) == 0.9
    assert calculate_churn_risk(200) == 0.85
    assert calculate_churn_risk(100) == 0.6
    assert calculate_churn_risk(70) == 0.4
    assert calculate_churn_risk(45) == 0.2
    assert calculate_churn_risk(15) == 0.05
