"""Phase 3: empty guidance, keywords, demo scenarios, cache, startup."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError

from src.app.main import create_app
from src.app.schemas.recommend import RecommendRequest
from src.config import Settings
from src.data.ingest import CatalogCacheError
from src.demo import SCENARIOS, run_scenario
from src.engine.recommend import recommend
from src.filtering.filters import filter_and_score
from src.filtering.scorer import keyword_hits
from src.observability import metrics
from src.preferences.normalize import extract_keywords, normalize_preferences


def test_empty_suggestions_are_specific(catalog):
    result = recommend(
        RecommendRequest(
            location="Atlantis",
            budget="low",
            cuisine=["Martian"],
            min_rating=4.9,
            top_k=5,
        ),
        catalog=catalog,
        settings=Settings(min_candidates=1, groq_api_key="", llm_api_key=""),
    )
    assert result.recommendations == []
    blob = " ".join(result.meta.suggestions).casefold()
    assert "atlantis" in blob or "location" in blob
    assert result.meta.filter_stage_counts.get("after_location") == 0
    snapshot = metrics.snapshot()
    assert snapshot["recommend_empty"] >= 1


def test_filter_stage_counts_recorded(catalog):
    prefs = normalize_preferences(
        RecommendRequest(
            location="Bangalore",
            budget="medium",
            cuisine=["Italian"],
            min_rating=4.0,
            top_k=5,
        )
    )
    result = filter_and_score(catalog.frame, prefs, Settings(min_candidates=1))
    assert result.stage_counts["catalog"] == 4
    assert result.stage_counts["after_location"] == 4
    assert result.stage_counts["after_cuisine"] >= 1
    assert result.stage_counts["returned"] == len(result.frame)


def test_romantic_keyword_matches_fine_dining():
    keys = extract_keywords("romantic date night", max_len=500)
    assert "romantic" in keys or "date night" in keys
    row = {
        "search_document": "Fine Place MG Road",
        "name": "Fine Place",
        "rest_type": "Fine Dining",
        "cuisine": ["Italian"],
    }
    import pandas as pd

    hits = keyword_hits(pd.Series(row), ["romantic"])
    assert "romantic" in hits


def test_family_friendly_matches_casual_dining(catalog):
    prefs = normalize_preferences(
        RecommendRequest(
            location="Bangalore",
            budget="medium",
            cuisine=[],
            min_rating=3.5,
            additional_preferences="family-friendly",
            top_k=5,
        )
    )
    result = filter_and_score(catalog.frame, prefs, Settings(min_candidates=1))
    dhaba = result.frame.loc[result.frame["name"] == "Family Dhaba"]
    assert not dhaba.empty
    hits = list(dhaba.iloc[0]["keyword_hits"] or [])
    assert hits


def test_demo_scenarios_on_fixture(catalog):
    settings = Settings(min_candidates=1, groq_api_key="", llm_api_key="")
    for scenario in SCENARIOS:
        result = run_scenario(scenario, catalog=catalog, settings=settings)
        if scenario.get("expect_empty"):
            assert result.recommendations == []
            assert result.meta.suggestions
        else:
            assert result.recommendations, scenario["id"]
            assert result.meta.source in {"llm", "fallback"}
            assert result.meta.latency_breakdown is not None


def test_recommend_cache_hit(catalog):
    settings = Settings(
        min_candidates=1,
        groq_api_key="",
        llm_api_key="",
        recommend_cache_ttl_seconds=60,
    )
    body = RecommendRequest(
        location="Bangalore",
        budget="medium",
        cuisine=["Italian"],
        min_rating=4.0,
        additional_preferences="cache-demo",
        top_k=3,
    )
    first = recommend(body, catalog=catalog, settings=settings)
    second = recommend(body, catalog=catalog, settings=settings)
    assert first.meta.cache_hit is False
    assert second.meta.cache_hit is True
    assert [item.id for item in first.recommendations] == [item.id for item in second.recommendations]


def test_budget_config_validation():
    with pytest.raises(ValidationError):
        Settings(budget_low_max=2000, budget_medium_max=500)


def test_startup_fails_when_catalog_missing(monkeypatch):
    def boom(cache_dir=None):
        raise CatalogCacheError("missing cache")

    monkeypatch.setattr("src.app.main.Catalog.load", boom)
    app = create_app()
    with pytest.raises(CatalogCacheError):
        with TestClient(app):
            pass
