"""Preference schema and normalization."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from src.app.schemas.recommend import RecommendRequest
from src.config import Settings
from src.data.clean import budget_band
from src.preferences.normalize import extract_keywords, normalize_cuisine_label, normalize_preferences


def test_budget_band_thresholds():
    assert budget_band(500, 500, 1500) == "low"
    assert budget_band(501, 500, 1500) == "medium"
    assert budget_band(1500, 500, 1500) == "medium"
    assert budget_band(1501, 500, 1500) == "high"
    assert budget_band(None, 500, 1500) == "unknown"


def test_cuisine_aliases():
    assert normalize_cuisine_label("North-Indian") == "north indian"
    assert normalize_cuisine_label("  Italian ") == "italian"


def test_normalize_from_request():
    req = RecommendRequest(
        location=" Bangalore ",
        budget="medium",
        cuisine=["Italian", "North Indian"],
        min_rating=4.0,
        additional_preferences="family-friendly, quick service",
        top_k=3,
    )
    prefs = normalize_preferences(req)
    assert prefs.location == "Bangalore"
    assert prefs.budget == "medium"
    assert prefs.cuisines == ["italian", "north indian"]
    assert "family-friendly" in prefs.keywords
    assert "quick service" in prefs.keywords
    assert prefs.top_k == 3


def test_empty_cuisine_means_any():
    prefs = normalize_preferences(
        {"location": "Bangalore", "budget": "low", "cuisine": [], "min_rating": 3.5, "top_k": 5}
    )
    assert prefs.cuisines == []


def test_invalid_budget_enum():
    with pytest.raises(ValidationError):
        RecommendRequest(location="Bangalore", budget="expensive")


def test_min_rating_out_of_range():
    with pytest.raises(ValidationError):
        RecommendRequest(location="Bangalore", budget="low", min_rating=6)


def test_top_k_bounds():
    with pytest.raises(ValidationError):
        RecommendRequest(location="Bangalore", budget="low", top_k=0)
    with pytest.raises(ValidationError):
        RecommendRequest(location="Bangalore", budget="low", top_k=50)


def test_extract_keywords_truncates_known_phrases():
    settings = Settings()
    keys = extract_keywords("family-friendly and a rooftop", max_len=settings.max_additional_preferences_chars)
    assert "family-friendly" in keys
    assert "rooftop" in keys


def test_extract_date_night_and_cafe_phrases():
    keys = extract_keywords("date night at a cafe with outdoor seating", max_len=500)
    assert "date night" in keys
    assert "cafe" in keys
    assert "outdoor" in keys
