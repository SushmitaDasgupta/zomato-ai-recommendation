"""Download, clean, and cache the restaurant catalog."""

from __future__ import annotations

import argparse
import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

import pandas as pd

from src.config import get_settings
from src.data.clean import clean_frame
from src.data.mapping import SOURCE_LOAD_COLUMNS, SchemaMappingError, assert_source_columns
from src.data.schema import CACHE_SCHEMA_VERSION, CANONICAL_COLUMNS

logger = logging.getLogger(__name__)

PARQUET_NAME = "restaurants.parquet"
METADATA_NAME = "metadata.json"


class CatalogCacheError(RuntimeError):
    """Missing or stale processed cache."""


def parquet_path(cache_dir: Path) -> Path:
    return cache_dir / PARQUET_NAME


def metadata_path(cache_dir: Path) -> Path:
    return cache_dir / METADATA_NAME


def load_metadata(cache_dir: Path) -> Optional[dict]:
    path = metadata_path(cache_dir)
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise CatalogCacheError(
            "Processed cache metadata is corrupt ({path}). Delete data/processed and re-run ingest.".format(
                path=path
            )
        ) from exc


def cache_is_fresh(cache_dir: Path, *, dataset_id: str) -> bool:
    meta = load_metadata(cache_dir)
    path = parquet_path(cache_dir)
    if meta is None or not path.exists():
        return False
    if meta.get("schema_version") != CACHE_SCHEMA_VERSION:
        logger.info("Cache schema %s != %s; will rebuild.", meta.get("schema_version"), CACHE_SCHEMA_VERSION)
        return False
    if meta.get("dataset_id") != dataset_id:
        logger.info("Cache dataset %s != %s; will rebuild.", meta.get("dataset_id"), dataset_id)
        return False
    return True


def _select_source_columns(df: pd.DataFrame) -> pd.DataFrame:
    keep = [c for c in SOURCE_LOAD_COLUMNS if c in df.columns]
    return df.loc[:, keep]


def load_source_csv(path: Path) -> pd.DataFrame:
    df = pd.read_csv(path)
    assert_source_columns(df.columns)
    return _select_source_columns(df)


def load_source_huggingface(dataset_id: str) -> pd.DataFrame:
    from datasets import load_dataset

    logger.info("Downloading Hugging Face dataset %s …", dataset_id)
    try:
        dataset = load_dataset(dataset_id, split="train")
    except Exception as exc:  # noqa: BLE001 — surface a setup-friendly error
        raise RuntimeError(
            "Failed to download {dataset_id}. Check network access, or pass --source path/to.csv. "
            "If a previous processed cache exists, Catalog.load() can still run offline.".format(
                dataset_id=dataset_id
            )
        ) from exc
    assert_source_columns(dataset.column_names)
    drop = [c for c in dataset.column_names if c not in SOURCE_LOAD_COLUMNS]
    if drop:
        dataset = dataset.remove_columns(drop)
    return dataset.to_pandas()


def write_cache(df: pd.DataFrame, cache_dir: Path, metadata: dict) -> Path:
    cache_dir.mkdir(parents=True, exist_ok=True)
    out = parquet_path(cache_dir)
    try:
        df.to_parquet(out, index=False)
    except Exception as exc:  # noqa: BLE001
        raise CatalogCacheError("Failed to write processed parquet to {out}".format(out=out)) from exc
    metadata_path(cache_dir).write_text(json.dumps(metadata, indent=2), encoding="utf-8")
    return out


def ingest(
    *,
    source: Optional[Path] = None,
    force: bool = False,
    cache_dir: Optional[Path] = None,
    dataset_id: Optional[str] = None,
) -> Path:
    settings = get_settings()
    cache_dir = Path(cache_dir) if cache_dir is not None else settings.resolved_cache_dir()
    dataset_id = dataset_id or settings.hf_dataset_id

    if not force and cache_is_fresh(cache_dir, dataset_id=dataset_id):
        logger.info("Fresh cache at %s — skipping download.", parquet_path(cache_dir))
        return parquet_path(cache_dir)

    if source is not None:
        df = load_source_csv(Path(source))
        origin = "csv:{0}".format(source)
    else:
        df = load_source_huggingface(dataset_id)
        origin = "huggingface:{0}".format(dataset_id)

    cleaned = clean_frame(
        df,
        low_max=settings.budget_low_max,
        medium_max=settings.budget_medium_max,
    )
    missing = [c for c in CANONICAL_COLUMNS if c not in cleaned.columns]
    if missing:
        raise SchemaMappingError("Canonical output missing columns: {0}".format(missing))

    metadata = {
        "schema_version": CACHE_SCHEMA_VERSION,
        "dataset_id": dataset_id,
        "source": origin,
        "row_count": int(len(cleaned)),
        "created_at": datetime.now(timezone.utc).isoformat(),
        "budget_bands": {
            "low_max": settings.budget_low_max,
            "medium_max": settings.budget_medium_max,
            "unit": "INR approximate cost for two",
        },
        "assumed_cost_unit": "INR cost for two (dataset scale; thresholds are configurable)",
    }
    path = write_cache(cleaned, cache_dir, metadata)
    logger.info("Wrote %s restaurants to %s", len(cleaned), path)
    return path


def main(argv: Optional[list] = None) -> None:
    logging.basicConfig(level=get_settings().log_level.upper(), format="%(levelname)s %(message)s")
    parser = argparse.ArgumentParser(description="Ingest and cache the restaurant catalog.")
    parser.add_argument("--source", type=Path, default=None, help="Optional local CSV instead of Hugging Face")
    parser.add_argument("--force", action="store_true", help="Rebuild cache even if it looks fresh")
    args = parser.parse_args(argv)
    ingest(source=args.source, force=args.force)


if __name__ == "__main__":
    main()
