"""API contract: validation errors, empty results, LLM + fallback cards."""

from __future__ import annotations

import json

from fastapi.testclient import TestClient

from src.app.main import create_app
from src.config import Settings
from src.engine.recommend import recommend
from src.app.schemas.recommend import RecommendRequest
from src.llm.exceptions import LLMError


class SequenceLLM:
    def __init__(self, outputs):
        self.outputs = list(outputs)
        self.calls = []

    def complete(self, messages, *, json_mode=True):
        self.calls.append({"messages": messages, "json_mode": json_mode})
        if not self.outputs:
            raise LLMError("no stubbed LLM outputs left")
        item = self.outputs.pop(0)
        if isinstance(item, Exception):
            raise item
        return item


def _id_named(catalog, name: str) -> str:
    return str(catalog.frame.loc[catalog.frame["name"] == name, "id"].iloc[0])


def test_cors_allows_local_next_origin(catalog):
    client = TestClient(create_app(catalog=catalog))
    response = client.get("/health", headers={"Origin": "http://localhost:3000"})
    assert response.status_code == 200
    assert response.headers.get("access-control-allow-origin") == "http://localhost:3000"


def test_health_ok(catalog):
    client = TestClient(create_app(catalog=catalog))
    response = client.get("/health")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert body["catalog_rows"] == 4
    assert body["llm"]["provider"] == "groq"
    assert body["llm"]["configured"] is False


def test_recommend_happy_path(catalog):
    client = TestClient(create_app(catalog=catalog))
    response = client.post(
        "/recommend",
        json={
            "location": "Bangalore",
            "budget": "medium",
            "cuisine": ["Italian"],
            "min_rating": 4.0,
            "additional_preferences": "family-friendly",
            "top_k": 5,
        },
    )
    assert response.status_code == 200
    body = response.json()
    assert body["meta"]["source"] == "fallback"
    assert body["recommendations"]
    first = body["recommendations"][0]
    for key in ("rank", "name", "cuisine", "rating", "estimated_cost", "location", "explanation"):
        assert key in first
    assert first["source"] == "fallback"


def test_invalid_budget_returns_400(catalog):
    client = TestClient(create_app(catalog=catalog))
    response = client.post(
        "/recommend",
        json={"location": "Bangalore", "budget": "expensive"},
    )
    assert response.status_code == 400
    assert "detail" in response.json()


def test_missing_location_returns_400(catalog):
    client = TestClient(create_app(catalog=catalog))
    response = client.post("/recommend", json={"budget": "low"})
    assert response.status_code == 400


def test_empty_payload_shape(catalog):
    client = TestClient(create_app(catalog=catalog))
    response = client.post(
        "/recommend",
        json={
            "location": "Atlantis",
            "budget": "low",
            "cuisine": ["Martian"],
            "min_rating": 4.9,
            "top_k": 5,
        },
    )
    assert response.status_code == 200
    body = response.json()
    assert body["recommendations"] == []
    assert body["meta"]["empty_reason"] == "no_restaurants_matched"
    assert body["meta"]["suggestions"]


def test_cards_include_explanation_from_engine(catalog):
    result = recommend(
        RecommendRequest(
            location="Bangalore",
            budget="high",
            cuisine=["Italian"],
            min_rating=4.0,
            top_k=5,
        ),
        catalog=catalog,
        settings=Settings(min_candidates=1, groq_api_key="", llm_api_key=""),
    )
    assert result.recommendations
    assert result.recommendations[0].explanation
    assert "budget" in result.recommendations[0].explanation.lower()
    assert result.meta.source == "fallback"


def test_recommend_uses_injected_llm(catalog):
    rest_id = _id_named(catalog, "Trattoria XYZ")
    payload = {
        "summary": "Italian picks that fit a medium budget in Bangalore.",
        "recommendations": [
            {
                "id": rest_id,
                "rank": 1,
                "explanation": "High rating and Italian cooking in Indiranagar at a medium cost.",
                "fit_notes": ["cuisine", "rating", "budget"],
            }
        ],
    }
    llm = SequenceLLM([json.dumps(payload)])
    client = TestClient(create_app(catalog=catalog, llm_client=llm))
    response = client.post(
        "/recommend",
        json={
            "location": "Bangalore",
            "budget": "medium",
            "cuisine": ["Italian"],
            "min_rating": 4.0,
            "top_k": 5,
        },
    )
    assert response.status_code == 200
    body = response.json()
    assert body["meta"]["source"] == "llm"
    assert body["summary"] == payload["summary"]
    assert body["recommendations"][0]["id"] == rest_id
    assert body["recommendations"][0]["source"] == "llm"
    assert body["recommendations"][0]["name"] == "Trattoria XYZ"
    assert llm.calls


def test_meta_filters(catalog):
    client = TestClient(create_app(catalog=catalog))
    response = client.get("/meta/filters")
    assert response.status_code == 200
    body = response.json()
    assert body["cities"] == ["Bangalore"]
    assert "Indiranagar" in body["locations"]
    assert "Bangalore" not in body["locations"]
    assert body["default_location"] in body["locations"]
    assert "Italian" in body["cuisines"]
    assert "Chinese" in body["cuisines"]
    assert body["budget_bands"] == ["low", "medium", "high"]
    assert body["budget_bounds"]["low_max"] == 500
    assert body["catalog_rows"] == 4
    assert body["additional_preference_hints"]


def test_meta_filters_without_catalog():
    client = TestClient(create_app(load_catalog=False))
    response = client.get("/meta/filters")
    assert response.status_code == 503


def test_health_degraded_without_catalog():
    client = TestClient(create_app(load_catalog=False))
    response = client.get("/health")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "degraded"
    assert "metrics" in body


def test_request_id_echoed(catalog):
    client = TestClient(create_app(catalog=catalog))
    response = client.post(
        "/recommend",
        headers={"X-Request-ID": "walkthrough-1"},
        json={
            "location": "Bangalore",
            "budget": "medium",
            "cuisine": ["Italian"],
            "min_rating": 4.0,
            "top_k": 5,
        },
    )
    assert response.status_code == 200
    assert response.headers["x-request-id"] == "walkthrough-1"
    assert response.json()["meta"]["request_id"] == "walkthrough-1"
    assert response.json()["meta"]["latency_breakdown"]["total_ms"] >= 0
    assert "after_location" in response.json()["meta"]["filter_stage_counts"]


def test_cors_allows_frontend_origin(catalog):
    client = TestClient(create_app(catalog=catalog))
    response = client.options(
        "/health",
        headers={
            "Origin": "http://localhost:3000",
            "Access-Control-Request-Method": "GET",
        },
    )
    assert response.headers.get("access-control-allow-origin") == "http://localhost:3000"
