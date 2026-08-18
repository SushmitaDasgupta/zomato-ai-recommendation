"""Pre-rank scorer stability and NaN guards."""

from __future__ import annotations

import pandas as pd

from src.app.schemas.recommend import RecommendRequest
from src.filtering.scorer import budget_fit_score, score_frame
from src.preferences.normalize import normalize_preferences


def test_budget_fit_adjacent():
    assert budget_fit_score("medium", "medium") == 1.0
    assert budget_fit_score("low", "medium") == 0.5
    assert budget_fit_score("unknown", "low") == 0.0


def test_score_no_nans_and_stable_order():
    prefs = normalize_preferences(
        RecommendRequest(location="Bangalore", budget="medium", cuisine=["Italian"], min_rating=3.5, top_k=5)
    )
    frame = pd.DataFrame(
        [
            {
                "id": "r-b",
                "name": "B",
                "location": "Indiranagar",
                "city": "Bangalore",
                "cuisine": ["Italian"],
                "rating": 4.4,
                "cost_for_two": 1200,
                "budget_band": "medium",
                "votes": 10,
                "rest_type": "Casual Dining",
                "search_document": "B Italian Indiranagar",
            },
            {
                "id": "r-a",
                "name": "A",
                "location": "Indiranagar",
                "city": "Bangalore",
                "cuisine": ["Italian"],
                "rating": 4.4,
                "cost_for_two": 1200,
                "budget_band": "medium",
                "votes": 10,
                "rest_type": "Casual Dining",
                "search_document": "A Italian Indiranagar",
            },
        ]
    )
    scored = score_frame(frame, prefs)
    assert scored["match_score"].notna().all()
    assert list(scored["id"]) == ["r-a", "r-b"]


def test_single_row_score():
    prefs = normalize_preferences(
        RecommendRequest(location="Bangalore", budget="low", cuisine=[], min_rating=0, top_k=1)
    )
    frame = pd.DataFrame(
        [
            {
                "id": "r-1",
                "name": "Solo",
                "location": "Koramangala",
                "city": "Bangalore",
                "cuisine": ["Chinese"],
                "rating": 3.0,
                "cost_for_two": 250,
                "budget_band": "low",
                "votes": None,
                "rest_type": "Quick Bites",
                "search_document": "Solo Chinese",
            }
        ]
    )
    scored = score_frame(frame, prefs)
    assert len(scored) == 1
    assert scored.loc[0, "match_score"] >= 0
    assert pd.notna(scored.loc[0, "match_score"])
