"""In-memory restaurant catalog loaded from the processed cache."""

from __future__ import annotations

from pathlib import Path
from typing import List, Optional

import pandas as pd

from src.config import get_settings
from src.data.ingest import CatalogCacheError, load_metadata, parquet_path
from src.data.schema import CACHE_SCHEMA_VERSION, REQUIRED_CANONICAL


def cuisine_items(cell) -> List[str]:
    """Normalize a cuisine cell (list, ndarray, or scalar) to python strings.

    Parquet round-trip stores cuisine lists as numpy arrays; treating those as a
    single cell made ``list_cuisines()`` crash on ``if item:``.
    """
    if cell is None:
        return []
    try:
        if pd.isna(cell):
            return []
    except (ValueError, TypeError):
        pass
    if isinstance(cell, str):
        text = cell.strip()
        return [text] if text else []
    if isinstance(cell, (list, tuple)):
        items = list(cell)
    elif hasattr(cell, "tolist"):
        converted = cell.tolist()
        items = converted if isinstance(converted, list) else [converted]
    else:
        items = [cell]
    out: List[str] = []
    for item in items:
        if item is None:
            continue
        try:
            if pd.isna(item):
                continue
        except (ValueError, TypeError):
            pass
        text = str(item).strip()
        if text and text.casefold() not in {"nan", "none"}:
            out.append(text)
    return out


class Catalog:
    def __init__(self, frame: pd.DataFrame, metadata: Optional[dict] = None):
        self.frame = frame
        self.metadata = metadata or {}

    @classmethod
    def load(cls, cache_dir: Optional[Path] = None) -> "Catalog":
        settings = get_settings()
        cache_dir = Path(cache_dir) if cache_dir is not None else settings.resolved_cache_dir()
        path = parquet_path(cache_dir)
        if not path.exists():
            raise CatalogCacheError(
                "Processed catalog not found at {path}. Run: python -m src.data.ingest".format(path=path)
            )
        try:
            frame = pd.read_parquet(path)
        except Exception as exc:  # noqa: BLE001
            raise CatalogCacheError(
                "Processed cache at {path} is unreadable. Delete it and re-run ingest.".format(path=path)
            ) from exc

        meta = load_metadata(cache_dir)
        if meta is not None and meta.get("schema_version") != CACHE_SCHEMA_VERSION:
            raise CatalogCacheError(
                "Stale catalog schema {found} (expected {expected}). Re-run: python -m src.data.ingest --force".format(
                    found=meta.get("schema_version"),
                    expected=CACHE_SCHEMA_VERSION,
                )
            )
        missing = [c for c in REQUIRED_CANONICAL if c not in frame.columns]
        if missing:
            raise CatalogCacheError("Catalog missing canonical fields: {0}".format(missing))
        if "cuisine" in frame.columns:
            frame = frame.copy()
            frame["cuisine"] = frame["cuisine"].map(cuisine_items)
        return cls(frame, metadata=meta)

    def list_locations(self) -> List[str]:
        values = self.frame["location"].dropna().astype(str).str.strip()
        return sorted({value for value in values.tolist() if value})

    def list_cities(self) -> List[str]:
        if "city" not in self.frame.columns:
            return []
        values = self.frame["city"].dropna().astype(str).str.strip()
        return sorted({value for value in values.tolist() if value})

    def list_cuisines(self) -> List[str]:
        seen = set()
        for cell in self.frame["cuisine"].dropna():
            for item in cuisine_items(cell):
                seen.add(item)
        return sorted(seen)

    def facet_locations(self, *, limit: Optional[int] = None) -> List[str]:
        """Neighbourhoods from the catalog `location` column, ranked by restaurant count.

        Does not include `city`. This dataset's city is a constant (Bangalore);
        Neighborhood autocomplete must use localities such as BTM or Indiranagar.
        """
        if "location" not in self.frame.columns:
            return []
        counts = self.frame["location"].dropna().astype(str).str.strip().value_counts()
        names = [name for name in counts.index.tolist() if name]
        if limit is not None:
            names = names[: int(limit)]
        return names

    def facet_cuisines(self, *, limit: Optional[int] = None) -> List[str]:
        from collections import Counter

        counts: Counter[str] = Counter()
        for cell in self.frame["cuisine"].dropna():
            for item in cuisine_items(cell):
                counts[item] += 1
        names = [name for name, _ in counts.most_common()]
        if limit is not None:
            names = names[: int(limit)]
        return names

    def default_location(self) -> Optional[str]:
        locations = self.facet_locations(limit=1)
        return locations[0] if locations else None

    def query(self, location: Optional[str] = None, limit: Optional[int] = None) -> pd.DataFrame:
        """Simple location/city contains match (Phase 0 smoke / later filter foundation)."""
        result = self.frame
        if location:
            needle = location.strip().casefold()
            loc = self.frame["location"].fillna("").astype(str).str.casefold()
            city = self.frame["city"].fillna("").astype(str).str.casefold()
            result = self.frame[loc.str.contains(needle, regex=False) | city.str.contains(needle, regex=False)]
        if limit is not None:
            result = result.head(limit)
        return result.reset_index(drop=True)
