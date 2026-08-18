from __future__ import annotations

from pathlib import Path

import pytest

from src.config import Settings, get_settings
from src.data.catalog import Catalog
from src.data.ingest import ingest
from src.observability import metrics, reset_recommend_cache

FIXTURE = Path(__file__).parent / "fixtures" / "restaurants_sample.csv"


@pytest.fixture(autouse=True)
def disable_live_llm(monkeypatch):
    """CI and local tests must not call Groq. Empty keys beat values in .env."""
    monkeypatch.setenv("GROQ_API_KEY", "")
    monkeypatch.setenv("LLM_API_KEY", "")
    get_settings.cache_clear()
    metrics.reset()
    reset_recommend_cache()
    yield
    get_settings.cache_clear()
    metrics.reset()
    reset_recommend_cache()


@pytest.fixture
def catalog(tmp_path) -> Catalog:
    cache_dir = tmp_path / "processed"
    ingest(source=FIXTURE, force=True, cache_dir=cache_dir)
    return Catalog.load(cache_dir=cache_dir)


@pytest.fixture
def settings() -> Settings:
    return Settings(min_candidates=1, groq_api_key="", llm_api_key="")
