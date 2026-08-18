"""Groq OpenAI-compatible client payload and error mapping."""

from __future__ import annotations

import json

import httpx
import pytest

from src.config import Settings
from src.llm.client import OpenAICompatibleClient, build_llm_client
from src.llm.exceptions import LLMError, LLMTimeoutError
from src.llm.prompts import SYSTEM_PROMPT, build_messages
from src.preferences.normalize import normalize_preferences
from src.app.schemas.recommend import RecommendRequest


def test_client_posts_json_mode_to_groq():
    captured = {}

    def handler(request: httpx.Request) -> httpx.Response:
        captured["url"] = str(request.url)
        captured["body"] = json.loads(request.content)
        captured["auth"] = request.headers.get("Authorization")
        return httpx.Response(
            200,
            json={"choices": [{"message": {"content": '{"summary": "ok", "recommendations": []}'}}]},
        )

    client = OpenAICompatibleClient(
        api_key="gsk_test",
        base_url="https://api.groq.com/openai/v1",
        model="llama-3.1-8b-instant",
        transport=httpx.MockTransport(handler),
        max_retries=0,
    )
    text = client.complete([{"role": "user", "content": "hi"}], json_mode=True)
    assert "summary" in text
    assert captured["url"] == "https://api.groq.com/openai/v1/chat/completions"
    assert captured["auth"] == "Bearer gsk_test"
    assert captured["body"]["model"] == "llama-3.1-8b-instant"
    assert captured["body"]["response_format"] == {"type": "json_object"}
    assert 0.2 <= captured["body"]["temperature"] <= 0.4


def test_client_maps_http_error():
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(401, text="invalid api key")

    client = OpenAICompatibleClient(
        api_key="bad",
        base_url="https://api.groq.com/openai/v1",
        model="llama-3.1-8b-instant",
        transport=httpx.MockTransport(handler),
        max_retries=0,
    )
    with pytest.raises(LLMError, match="401"):
        client.complete([{"role": "user", "content": "hi"}])


def test_client_timeout():
    def handler(request: httpx.Request) -> httpx.Response:
        raise httpx.ReadTimeout("slow")

    client = OpenAICompatibleClient(
        api_key="gsk_test",
        base_url="https://api.groq.com/openai/v1",
        model="llama-3.1-8b-instant",
        transport=httpx.MockTransport(handler),
        max_retries=0,
    )
    with pytest.raises(LLMTimeoutError):
        client.complete([{"role": "user", "content": "hi"}])


def test_build_client_without_key_returns_none():
    assert build_llm_client(Settings(groq_api_key="", llm_api_key="")) is None


def test_build_client_prefers_groq_key():
    client = build_llm_client(
        Settings(
            llm_provider="groq",
            groq_api_key="gsk_live",
            llm_api_key="sk-openai",
            llm_model="llama-3.1-8b-instant",
        )
    )
    assert client is not None
    assert client.api_key == "gsk_live"
    assert client.base_url == "https://api.groq.com/openai/v1"
    assert client.model == "llama-3.1-8b-instant"


def test_system_prompt_forbids_invention(catalog):
    prefs = normalize_preferences(
        RecommendRequest(location="Bangalore", budget="medium", cuisine=["Italian"], min_rating=4.0, top_k=3)
    )
    messages = build_messages(prefs, catalog.frame, Settings(max_candidates_for_llm=5))
    assert messages[0]["role"] == "system"
    assert messages[0]["content"] == SYSTEM_PROMPT
    assert "Do not invent" in SYSTEM_PROMPT
    assert "JSON" in messages[1]["content"]
    assert "Trattoria XYZ" in messages[1]["content"]
