"""Phase 0: ingest, cache, and catalog smoke checks (offline fixture)."""

from __future__ import annotations

from pathlib import Path

from src.data.catalog import Catalog, cuisine_items
from src.data.ingest import ingest, parquet_path
from src.data.schema import REQUIRED_CANONICAL

FIXTURE = Path(__file__).parent / "fixtures" / "restaurants_sample.csv"


def test_cuisine_items_handles_numpy_style_lists():
    assert cuisine_items(["Italian", "Continental"]) == ["Italian", "Continental"]
    assert cuisine_items("Chinese") == ["Chinese"]
    assert cuisine_items(None) == []


def test_ingest_and_catalog_from_fixture(tmp_path):
    cache_dir = tmp_path / "processed"
    ingest(source=FIXTURE, force=True, cache_dir=cache_dir)

    assert parquet_path(cache_dir).exists()
    catalog = Catalog.load(cache_dir=cache_dir)
    df = catalog.frame

    assert len(df) == 4
    assert all(col in df.columns for col in REQUIRED_CANONICAL)
    assert catalog.query("Bangalore").shape[0] == 4
    assert catalog.list_cities() == ["Bangalore"]
    assert "Indiranagar" in catalog.list_locations()
    assert "Bangalore" not in catalog.facet_locations()
    assert catalog.default_location() in catalog.list_locations()
    assert set(catalog.facet_locations()) == set(catalog.list_locations())
    assert "Italian" in catalog.list_cuisines()
    assert "Chinese" in catalog.list_cuisines()
    assert set(df["budget_band"]) <= {"low", "medium", "high", "unknown"}
    assert all(isinstance(cell, list) for cell in df["cuisine"])


def test_second_ingest_reuses_fresh_cache(tmp_path):
    cache_dir = tmp_path / "processed"
    first = ingest(source=FIXTURE, force=True, cache_dir=cache_dir)
    mtime = first.stat().st_mtime
    second = ingest(source=FIXTURE, force=False, cache_dir=cache_dir)
    assert second == first
    assert second.stat().st_mtime == mtime
