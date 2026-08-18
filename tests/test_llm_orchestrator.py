"""Orchestrator: LLM happy path, grounding, empty skip, fallback."""

from __future__ import annotations

import json

from src.app.schemas.recommend import RecommendRequest
from src.config import Settings
from src.engine.recommend import recommend
from src.llm.exceptions import LLMError, LLMTimeoutError
from src.llm.prompts import serialize_candidates


class SequenceLLM:
    def __init__(self, outputs):
        self.outputs = list(outputs)
        self.calls = []

    def complete(self, messages, *, json_mode=True):
        self.calls.append(messages)
        if not self.outputs:
            raise LLMError("no stubbed LLM outputs left")
        item = self.outputs.pop(0)
        if isinstance(item, Exception):
            raise item
        return item


def _id_named(catalog, name: str) -> str:
    return str(catalog.frame.loc[catalog.frame["name"] == name, "id"].iloc[0])


def _offline_settings(**kwargs) -> Settings:
    values = {"min_candidates": 1, "groq_api_key": "", "llm_api_key": ""}
    values.update(kwargs)
    return Settings(**values)


def test_llm_happy_path_joins_catalog_fields(catalog):
    rest_id = _id_named(catalog, "Trattoria XYZ")
    llm = SequenceLLM(
        [
            json.dumps(
                {
                    "summary": "Italian picks with solid ratings in Bangalore.",
                    "recommendations": [
                        {
                            "id": rest_id,
                            "rank": 1,
                            "explanation": "Matches Italian and a medium budget with a 4.4 rating.",
                            "fit_notes": ["cuisine", "budget"],
                        }
                    ],
                }
            )
        ]
    )
    result = recommend(
        RecommendRequest(
            location="Bangalore",
            budget="medium",
            cuisine=["Italian"],
            min_rating=4.0,
            additional_preferences="family-friendly",
            top_k=5,
        ),
        catalog=catalog,
        settings=_offline_settings(),
        llm_client=llm,
    )
    assert result.meta.source == "llm"
    assert result.summary.startswith("Italian picks")
    assert result.recommendations[0].source == "llm"
    assert result.recommendations[0].name == "Trattoria XYZ"
    assert result.recommendations[0].rating == 4.4
    assert result.recommendations[0].estimated_cost == 1200
    assert "medium budget" in result.recommendations[0].explanation
    assert llm.calls


def test_llm_ignores_hallucinated_name_and_rating(catalog):
    rest_id = _id_named(catalog, "Trattoria XYZ")
    llm = SequenceLLM(
        [
            json.dumps(
                {
                    "summary": "A match.",
                    "recommendations": [
                        {
                            "id": rest_id,
                            "rank": 1,
                            "name": "Totally Fake Trattoria",
                            "rating": 1.0,
                            "explanation": "Catalog fields must win.",
                        }
                    ],
                }
            )
        ]
    )
    result = recommend(
        RecommendRequest(location="Bangalore", budget="medium", cuisine=["Italian"], min_rating=4.0, top_k=1),
        catalog=catalog,
        settings=_offline_settings(),
        llm_client=llm,
    )
    item = result.recommendations[0]
    assert item.name == "Trattoria XYZ"
    assert item.rating == 4.4
    assert item.estimated_cost == 1200


def test_hallucinated_id_dropped_and_backfilled(catalog):
    real_id = _id_named(catalog, "Trattoria XYZ")
    llm = SequenceLLM(
        [
            json.dumps(
                {
                    "summary": "Mixed list.",
                    "recommendations": [
                        {"id": "r-does-not-exist", "rank": 1, "explanation": "ghost"},
                        {"id": real_id, "rank": 2, "explanation": "Real trattoria fit."},
                    ],
                }
            )
        ]
    )
    result = recommend(
        RecommendRequest(location="Bangalore", budget="medium", cuisine=["Italian"], min_rating=4.0, top_k=2),
        catalog=catalog,
        settings=_offline_settings(min_candidates=5),
        llm_client=llm,
    )
    ids = [item.id for item in result.recommendations]
    names = [item.name for item in result.recommendations]
    assert "r-does-not-exist" not in ids
    assert real_id in ids
    assert "Trattoria XYZ" in names
    assert result.recommendations[0].source == "llm"
    assert result.recommendations[0].explanation == "Real trattoria fit."
    if len(result.recommendations) > 1:
        assert result.recommendations[1].source == "fallback"


def test_llm_error_falls_back(catalog):
    llm = SequenceLLM([LLMTimeoutError("timed out")])
    result = recommend(
        RecommendRequest(location="Bangalore", budget="medium", cuisine=["Italian"], min_rating=4.0, top_k=5),
        catalog=catalog,
        settings=_offline_settings(),
        llm_client=llm,
    )
    assert result.recommendations
    assert result.meta.source == "fallback"
    assert result.meta.fallback_reason == "llm_error"
    assert all(item.source == "fallback" for item in result.recommendations)
    assert result.summary


def test_invalid_json_then_repair(catalog):
    rest_id = _id_named(catalog, "Trattoria XYZ")
    good = json.dumps(
        {
            "summary": "Repaired.",
            "recommendations": [{"id": rest_id, "rank": 1, "explanation": "Recovered JSON."}],
        }
    )
    llm = SequenceLLM(["this is not json", good])
    result = recommend(
        RecommendRequest(location="Bangalore", budget="medium", cuisine=["Italian"], min_rating=4.0, top_k=1),
        catalog=catalog,
        settings=_offline_settings(),
        llm_client=llm,
    )
    assert result.meta.source == "llm"
    assert result.recommendations[0].explanation == "Recovered JSON."
    assert len(llm.calls) == 2


def test_invalid_json_both_attempts_fallback(catalog):
    llm = SequenceLLM(["nope", "still nope"])
    result = recommend(
        RecommendRequest(location="Bangalore", budget="medium", cuisine=["Italian"], min_rating=4.0, top_k=5),
        catalog=catalog,
        settings=_offline_settings(),
        llm_client=llm,
    )
    assert result.meta.source == "fallback"
    assert result.meta.fallback_reason == "invalid_json"
    assert result.recommendations


def test_empty_results_skip_llm(catalog):
    llm = SequenceLLM([LLMError("should not be called")])
    result = recommend(
        RecommendRequest(location="Atlantis", budget="low", cuisine=["Martian"], min_rating=4.9, top_k=5),
        catalog=catalog,
        settings=_offline_settings(),
        llm_client=llm,
    )
    assert result.recommendations == []
    assert result.meta.empty_reason == "no_restaurants_matched"
    assert llm.calls == []


def test_missing_key_falls_back_without_client(catalog):
    result = recommend(
        RecommendRequest(location="Bangalore", budget="medium", cuisine=["Italian"], min_rating=4.0, top_k=5),
        catalog=catalog,
        settings=_offline_settings(),
    )
    assert result.recommendations
    assert result.meta.source == "fallback"
    assert result.meta.fallback_reason == "missing_api_key"


def test_prompt_candidates_are_capped(catalog):
    settings = _offline_settings(max_candidates_for_llm=2)
    rows = serialize_candidates(catalog.frame, limit=settings.max_candidates_for_llm)
    assert len(rows) <= 2
    assert {"id", "name", "cuisine", "rating", "cost_for_two", "location", "type"} <= set(rows[0])
