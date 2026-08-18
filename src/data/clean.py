"""Cleaning and derived-field helpers for the restaurant catalog."""

from __future__ import annotations

import hashlib
import html
import re
from typing import Iterable, List, Optional

import pandas as pd

from src.data.mapping import DATASET_CITY

_TAG_RE = re.compile(r"<[^>]+>")
_NON_NUMERIC = {"", "nan", "none", "null", "new", "-", "na"}


def normalize_text(value) -> Optional[str]:
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return None
    text = html.unescape(str(value))
    text = _TAG_RE.sub(" ", text)
    text = " ".join(text.split()).strip()
    return text or None


def coerce_rating(value) -> Optional[float]:
    """Parse Zomato rates like ``4.1/5``, ``NEW``, ``-`` into 0–5 or null."""
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return None
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        rating = float(value)
        return rating if 0.0 <= rating <= 5.0 else None
    text = str(value).strip()
    if text.lower() in _NON_NUMERIC:
        return None
    text = text.split("/")[0].strip()
    try:
        rating = float(text)
    except ValueError:
        return None
    if 0.0 <= rating <= 5.0:
        return rating
    return None


def coerce_cost(value) -> Optional[float]:
    """Parse cost-for-two strings such as ``1,200`` or ``₹500``."""
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return None
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        return float(value)
    text = str(value).strip()
    text = text.replace(",", "").replace("₹", "").replace("Rs.", "").replace("Rs", "")
    text = " ".join(text.split())
    if text.lower() in _NON_NUMERIC:
        return None
    try:
        return float(text)
    except ValueError:
        return None


def yes_no_to_bool(value) -> Optional[bool]:
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return None
    if isinstance(value, bool):
        return value
    text = str(value).strip().lower()
    if text in {"yes", "true", "1"}:
        return True
    if text in {"no", "false", "0"}:
        return False
    return None


def split_cuisines(value) -> List[str]:
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return []
    if isinstance(value, (list, tuple)):
        parts = value
    else:
        parts = str(value).split(",")
    cleaned: List[str] = []
    seen = set()
    for part in parts:
        item = normalize_text(part)
        if not item:
            continue
        key = item.casefold()
        if key in seen:
            continue
        seen.add(key)
        cleaned.append(item)
    return cleaned


def budget_band(cost: Optional[float], low_max: float, medium_max: float) -> str:
    if cost is None or (isinstance(cost, float) and pd.isna(cost)):
        return "unknown"
    if cost <= low_max:
        return "low"
    if cost <= medium_max:
        return "medium"
    return "high"


def make_id(url, name, address, location, row_index: int) -> str:
    seed = normalize_text(url) or "|".join(
        part or ""
        for part in (normalize_text(name), normalize_text(address), normalize_text(location), str(row_index))
    )
    digest = hashlib.sha1(seed.encode("utf-8")).hexdigest()[:16]
    return "r-{0}".format(digest)


def search_document(name, location, city, cuisines: Iterable[str], rest_type, online_order, book_table) -> str:
    flags = []
    if online_order is True:
        flags.append("online order")
    if book_table is True:
        flags.append("book table")
    parts = [
        name or "",
        location or "",
        city or "",
        ", ".join(cuisines or []),
        rest_type or "",
        " ".join(flags),
    ]
    return " ".join(part for part in parts if part).strip()


def clean_frame(df: pd.DataFrame, *, low_max: float, medium_max: float) -> pd.DataFrame:
    """Map source rows to canonical restaurant records."""
    work = df.copy()
    work["name"] = work["name"].map(normalize_text)
    work["location"] = work["location"].map(normalize_text)
    work = work[work["name"].notna() & work["location"].notna()].copy()

    votes = pd.to_numeric(work["votes"], errors="coerce") if "votes" in work.columns else None
    urls = work["url"] if "url" in work.columns else pd.Series([None] * len(work), index=work.index)
    addresses = work["address"] if "address" in work.columns else pd.Series([None] * len(work), index=work.index)

    records = []
    for idx, row in work.iterrows():
        cuisines = split_cuisines(row.get("cuisines"))
        rating = coerce_rating(row.get("rate"))
        cost = coerce_cost(row.get("approx_cost(for two people)"))
        rest_type = normalize_text(row.get("rest_type"))
        address = normalize_text(row.get("address"))
        online_order = yes_no_to_bool(row.get("online_order"))
        book_table = yes_no_to_bool(row.get("book_table"))
        vote_val = None
        if votes is not None:
            raw_vote = votes.loc[idx]
            if pd.notna(raw_vote):
                vote_val = int(raw_vote)
        name = row["name"]
        location = row["location"]
        records.append(
            {
                "id": make_id(urls.loc[idx] if urls is not None else None, name, address, location, int(idx)),
                "name": name,
                "location": location,
                "city": DATASET_CITY,
                "cuisine": cuisines,
                "rating": rating,
                "cost_for_two": cost,
                "budget_band": budget_band(cost, low_max, medium_max),
                "votes": vote_val,
                "rest_type": rest_type,
                "online_order": online_order,
                "book_table": book_table,
                "address": address,
                "search_document": search_document(
                    name, location, DATASET_CITY, cuisines, rest_type, online_order, book_table
                ),
            }
        )

    cleaned = pd.DataFrame.from_records(records)
    cleaned = cleaned.drop_duplicates(subset=["id"]).reset_index(drop=True)
    return cleaned
