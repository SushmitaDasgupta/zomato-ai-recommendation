"""Hard filters and relaxation policy for restaurant candidates."""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Dict, List, Sequence

import pandas as pd

from src.config import Settings, get_settings
from src.data.catalog import cuisine_items
from src.filtering.scorer import score_frame
from src.preferences.normalize import NormalizedPreferences, normalize_cuisine_label

logger = logging.getLogger(__name__)

ADJACENT_BANDS = {
    "low": ("low", "medium"),
    "medium": ("low", "medium", "high"),
    "high": ("medium", "high"),
}


@dataclass
class FilterResult:
    frame: pd.DataFrame
    filters_applied: List[str] = field(default_factory=list)
    relaxations_applied: List[str] = field(default_factory=list)
    candidates_considered: int = 0
    stage_counts: Dict[str, int] = field(default_factory=dict)


def _cuisine_labels(cell) -> List[str]:
    return [normalize_cuisine_label(item) for item in cuisine_items(cell)]


def filter_location(df: pd.DataFrame, location: str) -> pd.DataFrame:
    if df.empty:
        return df
    needle = location.strip().casefold()
    loc = df["location"].fillna("").astype(str).str.casefold()
    city = df["city"].fillna("").astype(str).str.casefold()
    return df.loc[loc.str.contains(needle, regex=False) | city.str.contains(needle, regex=False)]


def filter_rating(df: pd.DataFrame, min_rating: float) -> pd.DataFrame:
    if df.empty:
        return df
    rating = pd.to_numeric(df["rating"], errors="coerce")
    return df.loc[rating.notna() & (rating >= min_rating)]


def filter_budget(df: pd.DataFrame, budget: str, *, adjacent: bool = False) -> pd.DataFrame:
    if df.empty:
        return df
    allowed = ADJACENT_BANDS[budget] if adjacent else (budget,)
    return df.loc[df["budget_band"].isin(allowed)]


def _cuisine_hit(labels: Sequence[str], requested: Sequence[str], *, broad: bool) -> bool:
    if not requested:
        return True
    for req in requested:
        for label in labels:
            if label == req:
                return True
            if broad and (req in label or label in req):
                return True
    return False


def filter_cuisine(df: pd.DataFrame, cuisines: Sequence[str], *, broad: bool = False) -> pd.DataFrame:
    if df.empty or not cuisines:
        return df
    requested = [normalize_cuisine_label(c) for c in cuisines if c]
    mask = df["cuisine"].map(lambda cell: _cuisine_hit(_cuisine_labels(cell), requested, broad=broad))
    return df.loc[mask.fillna(False)]


def filter_and_score(
    df: pd.DataFrame,
    prefs: NormalizedPreferences,
    settings: Settings | None = None,
) -> FilterResult:
    settings = settings or get_settings()
    applied: List[str] = []
    relaxations: List[str] = []
    counts: Dict[str, int] = {"catalog": int(len(df))}

    work = filter_location(df, prefs.location)
    applied.append("location")
    counts["after_location"] = int(len(work))

    rated = filter_rating(work, prefs.min_rating)
    applied.append("rating")
    counts["after_rating"] = int(len(rated))

    if prefs.cuisines:
        cuisine_strict = filter_cuisine(rated, prefs.cuisines, broad=False)
        applied.append("cuisine")
    else:
        cuisine_strict = rated
    counts["after_cuisine"] = int(len(cuisine_strict))

    budget_strict = filter_budget(cuisine_strict, prefs.budget, adjacent=False)
    applied.append("budget")
    counts["after_budget"] = int(len(budget_strict))
    work = budget_strict

    min_candidates = settings.min_candidates
    if len(work) < min_candidates:
        budget_adj = filter_budget(cuisine_strict, prefs.budget, adjacent=True)
        if len(budget_adj) > len(work):
            logger.info(
                "relaxation=budget_adjacent location=%s budget=%s before=%s after=%s",
                prefs.location,
                prefs.budget,
                len(work),
                len(budget_adj),
            )
            work = budget_adj
            relaxations.append("budget_adjacent")

    if len(work) < min_candidates and prefs.cuisines:
        cuisine_broad = filter_cuisine(rated, prefs.cuisines, broad=True)
        adjacent = "budget_adjacent" in relaxations
        budgeted = filter_budget(cuisine_broad, prefs.budget, adjacent=adjacent)
        if len(budgeted) > len(work):
            logger.info(
                "relaxation=cuisine_broad location=%s cuisine=%s before=%s after=%s",
                prefs.location,
                prefs.cuisines,
                len(work),
                len(budgeted),
            )
            work = budgeted
            relaxations.append("cuisine_broad")

    counts["after_relax"] = int(len(work))
    scored = score_frame(work, prefs)
    if not scored.empty and {"name", "location"}.issubset(scored.columns):
        scored = scored.drop_duplicates(subset=["name", "location"], keep="first")
    cap = settings.max_candidates_for_llm
    pool = scored.head(cap).reset_index(drop=True)
    counts["returned"] = int(len(pool))
    logger.info(
        "filter location=%s cuisine=%s budget=%s min_rating=%s stages=%s relaxations=%s",
        prefs.location,
        prefs.cuisines,
        prefs.budget,
        prefs.min_rating,
        counts,
        relaxations,
    )
    return FilterResult(
        frame=pool,
        filters_applied=applied,
        relaxations_applied=relaxations,
        candidates_considered=int(len(work)),
        stage_counts=counts,
    )


def empty_suggestions(
    prefs: NormalizedPreferences,
    stage_counts: Dict[str, int],
    relaxations: Sequence[str],
) -> List[str]:
    after_location = int(stage_counts.get("after_location") or 0)
    after_rating = int(stage_counts.get("after_rating") or 0)
    after_cuisine = int(stage_counts.get("after_cuisine") or 0)
    after_budget = int(stage_counts.get("after_budget") or 0)
    tips: List[str] = []

    if after_location == 0:
        tips.append(
            "No restaurants found in {0}. Try a well-supported city such as Bangalore, or a nearby locality.".format(
                prefs.location
            )
        )
    else:
        if prefs.cuisines and after_cuisine == 0:
            tips.append(
                "No {0} matches in {1}. Clear cuisine or pick a more common type (North Indian, Chinese, South Indian).".format(
                    ", ".join(prefs.cuisines),
                    prefs.location,
                )
            )
        if after_rating == 0:
            tips.append(
                "Nothing meets min rating {0}. Lower the rating (try 3.5 or below).".format(prefs.min_rating)
            )
        elif after_budget == 0:
            tips.append(
                "Nothing in the {0} budget band after the other filters. Try a wider budget.".format(prefs.budget)
            )
        if not tips:
            tips.append("Those filters are too tight together. Relax rating, budget, or cuisine.")

    if "budget_adjacent" in relaxations:
        tips.append("Already tried an adjacent budget band.")
    if "cuisine_broad" in relaxations:
        tips.append("Already tried a broader cuisine match.")

    generics = [
        "Try a different location",
        "Lower min_rating",
        "Widen budget",
    ]
    blob = " ".join(tips).casefold()
    for item in generics:
        if len(tips) >= 4:
            break
        token = item.split()[-1].casefold()
        if token in blob:
            continue
        tips.append(item)
    return tips
