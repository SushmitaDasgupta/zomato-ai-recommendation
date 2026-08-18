"""Normalize and validate user preferences before filtering."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import List, Mapping, Optional, Sequence, Union

from src.app.schemas.recommend import RecommendRequest
from src.config import Settings, get_settings

_SPACE_RE = re.compile(r"\s+")
_SPLIT_RE = re.compile(r"[,;/]+")
_TOKEN_RE = re.compile(r"[a-z0-9]+(?:'[a-z0-9]+)?")

CUISINE_ALIASES = {
    "nort indian": "north indian",
    "north-indian": "north indian",
    "northindian": "north indian",
    "south-indian": "south indian",
    "southindian": "south indian",
    "multi cuisine": "multi-cuisine",
    "multicuisine": "multi-cuisine",
    "indo chinese": "chinese",
    "indo-chinese": "chinese",
}

STOPWORDS = {
    "a",
    "an",
    "and",
    "for",
    "in",
    "of",
    "on",
    "or",
    "the",
    "to",
    "with",
    "want",
    "please",
}

# Longest phrases first so "family-friendly" wins over "family".
KNOWN_PREF_PHRASES = (
    "family-friendly",
    "family friendly",
    "kid friendly",
    "kids friendly",
    "fine dining",
    "casual dining",
    "quick service",
    "quick bites",
    "fast food",
    "online order",
    "book table",
    "pure veg",
    "north indian",
    "south indian",
    "date night",
    "live music",
    "pet friendly",
    "pet-friendly",
    "sunday brunch",
    "happy hour",
    "late night",
    "pocket friendly",
    "street food",
    "air conditioned",
    "work friendly",
    "group dining",
    "rooftop dining",
    "family",
    "kids",
    "children",
    "casual",
    "quick",
    "fast",
    "romantic",
    "date",
    "intimate",
    "outdoor",
    "rooftop",
    "garden",
    "terrace",
    "quiet",
    "ambience",
    "cafe",
    "café",
    "coffee",
    "bar",
    "pub",
    "lounge",
    "vegetarian",
    "vegan",
    "delivery",
    "takeaway",
    "buffet",
    "nightlife",
    "breakfast",
    "brunch",
    "dessert",
    "bakery",
    "wifi",
    "sports",
    "party",
    "celebration",
    "birthday",
    "healthy",
    "spicy",
    "authentic",
    "luxury",
    "premium",
    "cheap",
    "affordable",
    "seafood",
    "grill",
    "biryani",
    "cocktail",
    "drinks",
    "wine",
    "sheesha",
    "hookah",
)

KEYWORD_ALIASES = {
    "family friendly": "family-friendly",
    "kid friendly": "family-friendly",
    "kids friendly": "family-friendly",
    "kids": "family",
    "children": "family",
    "date night": "romantic",
    "date": "romantic",
    "café": "cafe",
    "coffee": "cafe",
    "fast food": "quick",
    "quick bites": "quick",
    "quick service": "quick",
    "fast": "quick",
    "takeaway": "delivery",
    "pocket friendly": "cheap",
    "affordable": "cheap",
    "premium": "luxury",
    "pet-friendly": "pet friendly",
    "rooftop dining": "rooftop",
}

# Catalog terms that should count as a hit for the user keyword.
KEYWORD_RELATED = {
    "family-friendly": ["family", "casual dining"],
    "family": ["casual dining", "family-friendly"],
    "romantic": ["fine dining", "intimate"],
    "quick": ["quick bites", "fast food", "casual"],
    "outdoor": ["rooftop", "garden", "terrace"],
    "cafe": ["cafe", "bakery", "coffee"],
    "luxury": ["fine dining"],
    "cheap": ["casual", "quick bites"],
    "rooftop": ["outdoor", "terrace", "garden"],
}

PREF_HINTS = (
    "family-friendly",
    "romantic",
    "quick",
    "outdoor",
    "cafe",
    "rooftop",
    "quiet",
    "live music",
    "pure veg",
)


@dataclass
class NormalizedPreferences:
    location: str
    budget: str
    cuisines: List[str]
    min_rating: float
    additional_preferences: str
    keywords: List[str] = field(default_factory=list)
    top_k: int = 5


def fold_text(value: str) -> str:
    text = " ".join(str(value).split()).strip()
    text = text.replace("-", " ")
    text = _SPACE_RE.sub(" ", text).casefold()
    return text.strip()


def normalize_cuisine_label(value: str) -> str:
    folded = fold_text(value)
    return CUISINE_ALIASES.get(folded, folded)


def canonical_keyword(phrase: str) -> str:
    folded = fold_text(phrase)
    return KEYWORD_ALIASES.get(folded, KEYWORD_ALIASES.get(phrase.casefold(), phrase))


def keyword_needles(keyword: str) -> List[str]:
    canonical = canonical_keyword(keyword)
    items = [keyword, canonical, *KEYWORD_RELATED.get(canonical, [])]
    out: List[str] = []
    seen = set()
    for item in items:
        folded = fold_text(item)
        if folded and folded not in seen:
            seen.add(folded)
            out.append(item)
    return out


def extract_keywords(text: str, *, max_len: int) -> List[str]:
    if not text:
        return []
    clipped = text[:max_len].casefold()
    found: List[str] = []
    remaining = clipped
    for phrase in KNOWN_PREF_PHRASES:
        key = phrase.casefold()
        if key in remaining:
            found.append(phrase)
            remaining = remaining.replace(key, " ")
    for token in _TOKEN_RE.findall(remaining):
        if token in STOPWORDS or len(token) < 4:
            continue
        if token not in found:
            found.append(token)
    # Preserve order, drop duplicates after aliasing.
    unique: List[str] = []
    seen = set()
    for item in found:
        key = fold_text(item)
        if key in seen:
            continue
        seen.add(key)
        unique.append(item)
    return unique


def _as_cuisine_list(value: Optional[Union[str, Sequence[str]]]) -> List[str]:
    if value is None:
        return []
    if isinstance(value, str):
        parts = _SPLIT_RE.split(value)
    else:
        parts = list(value)
    out: List[str] = []
    seen = set()
    for part in parts:
        label = normalize_cuisine_label(part)
        if not label or label in seen:
            continue
        seen.add(label)
        out.append(label)
    return out


def normalize_preferences(
    raw: Union[RecommendRequest, Mapping],
    settings: Optional[Settings] = None,
) -> NormalizedPreferences:
    settings = settings or get_settings()
    if isinstance(raw, RecommendRequest):
        location = raw.location
        budget = raw.budget
        cuisines = raw.cuisine
        min_rating = raw.min_rating
        additional = raw.additional_preferences or ""
        top_k = raw.top_k
    else:
        location = str(raw.get("location", ""))
        budget = str(raw.get("budget", "")).casefold()
        cuisines = raw.get("cuisine") or []
        min_rating = raw.get("min_rating", settings.min_rating_default)
        additional = raw.get("additional_preferences") or ""
        top_k = raw.get("top_k", settings.default_top_k)

    location_norm = " ".join(str(location).split()).strip()
    if not location_norm:
        raise ValueError("location is required")
    budget_norm = str(budget).strip().casefold()
    if budget_norm not in {"low", "medium", "high"}:
        raise ValueError("budget must be low, medium, or high")

    additional = str(additional)[: settings.max_additional_preferences_chars]
    top_k = int(top_k)
    if top_k < 1 or top_k > 10:
        raise ValueError("top_k must be between 1 and 10")
    min_rating = float(min_rating)
    if min_rating < 0 or min_rating > 5:
        raise ValueError("min_rating must be between 0 and 5")

    return NormalizedPreferences(
        location=location_norm,
        budget=budget_norm,
        cuisines=_as_cuisine_list(cuisines),
        min_rating=min_rating,
        additional_preferences=additional.strip(),
        keywords=extract_keywords(additional, max_len=settings.max_additional_preferences_chars),
        top_k=top_k,
    )
