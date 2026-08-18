"""Pre-rank scoring for filtered restaurant candidates."""

from __future__ import annotations

from typing import List

import pandas as pd

from src.data.catalog import cuisine_items
from src.preferences.normalize import NormalizedPreferences, fold_text, keyword_needles

SCORE_WEIGHTS = {
    "rating": 0.45,
    "votes": 0.20,
    "budget_fit": 0.20,
    "keyword": 0.15,
}

ADJACENT = {
    "low": {"medium"},
    "medium": {"low", "high"},
    "high": {"medium"},
}


def budget_fit_score(band: str, requested: str) -> float:
    if band == requested:
        return 1.0
    if band in ADJACENT.get(requested, set()):
        return 0.5
    return 0.0


def keyword_hits(row: pd.Series, keywords: List[str]) -> List[str]:
    if not keywords:
        return []
    blob = " ".join(
        [
            str(row.get("search_document") or ""),
            str(row.get("name") or ""),
            str(row.get("rest_type") or ""),
            " ".join(cuisine_items(row.get("cuisine"))),
        ]
    )
    blob_folded = fold_text(blob)
    hits = []
    for keyword in keywords:
        matched = False
        for needle in keyword_needles(keyword):
            folded = fold_text(needle)
            if folded and folded in blob_folded:
                matched = True
                break
        if matched:
            hits.append(keyword)
    return hits


def keyword_score(row: pd.Series, keywords: List[str]) -> float:
    if not keywords:
        return 0.0
    hits = keyword_hits(row, keywords)
    return min(1.0, len(hits) / len(keywords))


def _normalize_series(series: pd.Series, *, fill_missing: float = 0.0) -> pd.Series:
    numeric = pd.to_numeric(series, errors="coerce")
    present = numeric.dropna()
    if present.empty:
        return pd.Series(fill_missing, index=series.index, dtype=float)
    low, high = float(present.min()), float(present.max())
    if high == low:
        out = numeric.notna().astype(float)
        return out
    scaled = (numeric - low) / (high - low)
    return scaled.fillna(fill_missing)


def score_frame(df: pd.DataFrame, prefs: NormalizedPreferences) -> pd.DataFrame:
    if df.empty:
        empty = df.copy()
        empty["match_score"] = pd.Series(dtype=float)
        empty["keyword_hits"] = pd.Series(dtype=object)
        return empty

    work = df.copy()
    norm_rating = _normalize_series(work["rating"])
    votes = work["votes"] if "votes" in work.columns else 0
    norm_votes = _normalize_series(votes)
    budget = work["budget_band"].map(lambda band: budget_fit_score(str(band), prefs.budget)).astype(float)
    hits = work.apply(lambda row: keyword_hits(row, prefs.keywords), axis=1)
    keyword = hits.map(lambda items: min(1.0, len(items) / len(prefs.keywords)) if prefs.keywords else 0.0)

    work["keyword_hits"] = hits
    work["match_score"] = (
        SCORE_WEIGHTS["rating"] * norm_rating
        + SCORE_WEIGHTS["votes"] * norm_votes
        + SCORE_WEIGHTS["budget_fit"] * budget
        + SCORE_WEIGHTS["keyword"] * keyword
    )
    work["match_score"] = work["match_score"].fillna(0.0)
    work["_rating_sort"] = pd.to_numeric(work["rating"], errors="coerce").fillna(-1)
    work = work.sort_values(
        ["match_score", "_rating_sort", "id"],
        ascending=[False, False, True],
    )
    return work.drop(columns=["_rating_sort"]).reset_index(drop=True)
