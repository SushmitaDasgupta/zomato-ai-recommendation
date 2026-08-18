"""Filter match, miss, multi-cuisine, null ratings, and relaxation."""

from __future__ import annotations

import pandas as pd

from src.app.schemas.recommend import RecommendRequest
from src.config import Settings
from src.engine.recommend import recommend
from src.filtering.filters import filter_and_score
from src.preferences.normalize import normalize_preferences

def test_duplicate_listings_deduped_by_name_location():
    prefs = normalize_preferences(
        RecommendRequest(location="Bangalore", budget="medium", cuisine=["Italian"], min_rating=3.5, top_k=5)
    )
    frame = pd.DataFrame(
        [
            {
                "id": "r-1",
                "name": "Globe Grub",
                "location": "Marathahalli",
                "city": "Bangalore",
                "cuisine": ["Italian"],
                "rating": 4.8,
                "cost_for_two": 1300,
                "budget_band": "medium",
                "votes": 200,
                "rest_type": "Casual Dining",
                "search_document": "Globe Grub Italian",
            },
            {
                "id": "r-2",
                "name": "Globe Grub",
                "location": "Marathahalli",
                "city": "Bangalore",
                "cuisine": ["Italian"],
                "rating": 4.8,
                "cost_for_two": 1300,
                "budget_band": "medium",
                "votes": 50,
                "rest_type": "Casual Dining",
                "search_document": "Globe Grub Italian listed twice",
            },
            {
                "id": "r-3",
                "name": "Other Place",
                "location": "HSR",
                "city": "Bangalore",
                "cuisine": ["Italian"],
                "rating": 4.2,
                "cost_for_two": 900,
                "budget_band": "medium",
                "votes": 40,
                "rest_type": "Casual Dining",
                "search_document": "Other Place Italian",
            },
        ]
    )
    result = filter_and_score(frame, prefs, Settings(min_candidates=1, max_candidates_for_llm=10))
    names = list(result.frame["name"])
    assert names.count("Globe Grub") == 1
    assert "Other Place" in names


def test_hard_rating_filter(catalog):
    settings = Settings(min_candidates=1)
    response = recommend(
        RecommendRequest(
            location="Bangalore",
            budget="medium",
            cuisine=["Italian"],
            min_rating=4.0,
            top_k=5,
        ),
        catalog=catalog,
        settings=settings,
    )
    assert response.recommendations
    assert all(
        item.rating is not None and item.rating >= 4.0 for item in response.recommendations
    )
    names = {item.name for item in response.recommendations}
    assert "Family Dhaba" not in names
    assert "Cheap Eats" not in names


def test_null_rating_excluded(catalog):
    settings = Settings(min_candidates=1)
    response = recommend(
        RecommendRequest(
            location="Koramangala",
            budget="low",
            cuisine=["Chinese"],
            min_rating=3.5,
            top_k=5,
        ),
        catalog=catalog,
        settings=settings,
    )
    names = {item.name for item in response.recommendations}
    assert "Cheap Eats" not in names


def test_multi_cuisine_or_match(catalog):
    settings = Settings(min_candidates=1)
    prefs = normalize_preferences(
        RecommendRequest(
            location="Bangalore",
            budget="medium",
            cuisine=["Italian", "Chinese"],
            min_rating=3.5,
            top_k=5,
        )
    )
    result = filter_and_score(catalog.frame, prefs, settings)
    names = set(result.frame["name"])
    assert "Trattoria XYZ" in names
    assert "Family Dhaba" in names
    assert "Fine Place" not in names  # high budget, strict band


def test_no_match_empty(catalog):
    response = recommend(
        RecommendRequest(
            location="Atlantis",
            budget="low",
            cuisine=["Martian"],
            min_rating=4.9,
            top_k=5,
        ),
        catalog=catalog,
        settings=Settings(min_candidates=1),
    )
    assert response.recommendations == []
    assert response.meta.empty_reason == "no_restaurants_matched"
    assert response.meta.suggestions
    assert response.summary is None


def test_budget_relaxation_recorded(catalog):
    settings = Settings(min_candidates=5)
    response = recommend(
        RecommendRequest(
            location="Bangalore",
            budget="medium",
            cuisine=["Italian"],
            min_rating=4.0,
            top_k=5,
        ),
        catalog=catalog,
        settings=settings,
    )
    names = {item.name for item in response.recommendations}
    assert "Trattoria XYZ" in names
    assert "Fine Place" in names
    assert "budget_adjacent" in response.meta.relaxations_applied
    fine = next(item for item in response.recommendations if item.name == "Fine Place")
    assert fine.estimated_cost == 2400


def test_fewer_than_top_k(catalog):
    settings = Settings(min_candidates=1)
    response = recommend(
        RecommendRequest(
            location="Indiranagar",
            budget="medium",
            cuisine=["Italian"],
            min_rating=4.0,
            top_k=5,
        ),
        catalog=catalog,
        settings=settings,
    )
    assert 0 < len(response.recommendations) < 5
    assert [item.rank for item in response.recommendations] == list(
        range(1, len(response.recommendations) + 1)
    )
