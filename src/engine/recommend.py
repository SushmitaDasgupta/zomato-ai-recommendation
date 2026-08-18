"""Phase 2 orchestrator: filter → prompt → LLM → parse → assemble, with fallback."""

from __future__ import annotations

import logging
import time
from typing import List, Mapping, Optional, Sequence, Union

import pandas as pd

from src.app.schemas.recommend import (
    LatencyBreakdown,
    RecommendationItem,
    RecommendMeta,
    RecommendRequest,
    RecommendResponse,
)
from src.config import Settings, get_settings
from src.data.catalog import Catalog, cuisine_items
from src.filtering.filters import empty_suggestions, filter_and_score
from src.llm.client import LLMClient, build_llm_client
from src.llm.exceptions import LLMError, LLMParseError
from src.llm.parser import ParsedLLMOutput, parse_and_ground
from src.llm.prompts import build_messages, repair_messages
from src.observability import (
    metrics,
    preference_cache_key,
    recommend_cache,
    set_request_id,
)
from src.preferences.normalize import NormalizedPreferences, normalize_preferences

logger = logging.getLogger(__name__)


def _elapsed_ms(started: float) -> int:
    return int((time.perf_counter() - started) * 1000)


def _display_location(row: pd.Series) -> str:
    locality = str(row.get("location") or "").strip()
    city = str(row.get("city") or "").strip()
    if city and city.casefold() not in locality.casefold():
        return "{0}, {1}".format(locality, city) if locality else city
    return locality or city


def _display_cuisine(row: pd.Series) -> str:
    items = cuisine_items(row.get("cuisine"))
    return ", ".join(items) if items else "N/A"


def _optional_number(value):
    if value is None:
        return None
    try:
        if pd.isna(value):
            return None
    except (TypeError, ValueError):
        pass
    return float(value)


def _clip_explanation(text: str, settings: Settings) -> str:
    limit = settings.max_explanation_chars
    cleaned = " ".join(str(text or "").split()).strip()
    if len(cleaned) <= limit:
        return cleaned
    return cleaned[: limit - 1].rstrip() + "…"


def rule_explanation(row: pd.Series, prefs: NormalizedPreferences) -> str:
    rating = _optional_number(row.get("rating"))
    if rating is not None and rating >= 4.0:
        lead = "High rating"
    elif rating is not None:
        lead = "Meets your minimum rating"
    else:
        lead = "Matches your filters"
    cuisine_txt = ", ".join(prefs.cuisines) if prefs.cuisines else "your selected tastes"
    text = "{lead} and fits {budget} budget for {cuisine} in {location}.".format(
        lead=lead,
        budget=prefs.budget,
        cuisine=cuisine_txt,
        location=prefs.location,
    )
    hits = list(row.get("keyword_hits") or [])
    if hits:
        text += " Matches extra preferences ({0}).".format(", ".join(hits))
    return text


def _item_from_row(
    row: pd.Series,
    prefs: NormalizedPreferences,
    *,
    rank: int,
    explanation: str,
    source: str,
    fit_notes: Optional[Sequence[str]] = None,
) -> RecommendationItem:
    return RecommendationItem(
        rank=rank,
        id=str(row["id"]),
        name=str(row.get("name") or "Unknown"),
        cuisine=_display_cuisine(row),
        rating=_optional_number(row.get("rating")),
        estimated_cost=_optional_number(row.get("cost_for_two")),
        location=_display_location(row),
        explanation=explanation,
        match_score=round(float(row.get("match_score") or 0.0), 4),
        source=source,
        fit_notes=list(fit_notes or []),
    )


def assemble_items(
    frame: pd.DataFrame,
    prefs: NormalizedPreferences,
    *,
    source: str = "fallback",
) -> list:
    items = []
    for _, row in frame.head(prefs.top_k).iterrows():
        items.append(
            _item_from_row(
                row,
                prefs,
                rank=len(items) + 1,
                explanation=rule_explanation(row, prefs),
                source=source,
            )
        )
    return items


def _fallback_summary(prefs: NormalizedPreferences, count: int) -> Optional[str]:
    if count == 0:
        return None
    cuisine_txt = ", ".join(prefs.cuisines) if prefs.cuisines else "your selected tastes"
    return "Ranked by rating and budget fit for {cuisine} in {location}.".format(
        cuisine=cuisine_txt,
        location=prefs.location,
    )


def assemble_from_llm(
    frame: pd.DataFrame,
    prefs: NormalizedPreferences,
    parsed: ParsedLLMOutput,
    settings: Settings,
) -> List[RecommendationItem]:
    by_id = {str(row["id"]): row for _, row in frame.iterrows()}
    items: List[RecommendationItem] = []
    used = set()
    for pick in parsed.picks:
        row = by_id.get(pick.id)
        if row is None:
            continue
        explanation = _clip_explanation(pick.explanation, settings) or rule_explanation(row, prefs)
        items.append(
            _item_from_row(
                row,
                prefs,
                rank=len(items) + 1,
                explanation=explanation,
                source="llm",
                fit_notes=pick.fit_notes,
            )
        )
        used.add(pick.id)
        if len(items) >= prefs.top_k:
            return items

    for _, row in frame.iterrows():
        rest_id = str(row["id"])
        if rest_id in used:
            continue
        items.append(
            _item_from_row(
                row,
                prefs,
                rank=len(items) + 1,
                explanation=rule_explanation(row, prefs),
                source="fallback",
            )
        )
        used.add(rest_id)
        if len(items) >= prefs.top_k:
            break
    return items


def _llm_rank(
    client: LLMClient,
    frame: pd.DataFrame,
    prefs: NormalizedPreferences,
    settings: Settings,
) -> ParsedLLMOutput:
    allowed = [str(value) for value in frame["id"].tolist()]
    messages = build_messages(prefs, frame, settings)
    raw = client.complete(messages, json_mode=True)
    try:
        return parse_and_ground(raw, allowed, top_k=prefs.top_k)
    except LLMParseError:
        logger.info("LLM JSON parse failed; attempting one repair call")
    repaired = client.complete(repair_messages(messages, raw), json_mode=True)
    return parse_and_ground(repaired, allowed, top_k=prefs.top_k)


def recommend(
    raw: Union[RecommendRequest, Mapping],
    *,
    catalog: Catalog,
    settings: Optional[Settings] = None,
    llm_client: Optional[LLMClient] = None,
    request_id: Optional[str] = None,
) -> RecommendResponse:
    settings = settings or get_settings()
    rid = set_request_id(request_id)
    started = time.perf_counter()
    prefs = normalize_preferences(raw, settings)
    normalize_ms = _elapsed_ms(started)

    cache = recommend_cache(settings)
    cache_key = preference_cache_key(prefs)
    cached = cache.get(cache_key)
    if cached is not None:
        hit = cached.model_copy(deep=True)
        hit.meta.request_id = rid
        hit.meta.cache_hit = True
        metrics.record(
            source=hit.meta.source,
            empty=not hit.recommendations,
            fallback_reason=hit.meta.fallback_reason,
            relaxations=hit.meta.relaxations_applied,
            cache_hit=True,
        )
        logger.info(
            "recommend cache_hit=true request_id=%s source=%s empty=%s location=%s",
            rid,
            hit.meta.source,
            not hit.recommendations,
            prefs.location,
        )
        return hit

    t_filter = time.perf_counter()
    result = filter_and_score(catalog.frame, prefs, settings)
    filter_ms = _elapsed_ms(t_filter)
    empty = result.frame.empty
    parsed: Optional[ParsedLLMOutput] = None
    fallback_reason: Optional[str] = None
    source = "fallback"
    llm_ms = 0
    assemble_ms = 0

    if empty:
        items: List[RecommendationItem] = []
        summary = None
    else:
        client = llm_client if llm_client is not None else build_llm_client(settings)
        if client is None:
            fallback_reason = "missing_api_key"
            t_assemble = time.perf_counter()
            items = assemble_items(result.frame, prefs, source="fallback")
            summary = _fallback_summary(prefs, len(items))
            assemble_ms = _elapsed_ms(t_assemble)
        else:
            t_llm = time.perf_counter()
            try:
                parsed = _llm_rank(client, result.frame, prefs, settings)
                source = "llm"
            except LLMParseError as exc:
                llm_ms = _elapsed_ms(t_llm)
                fallback_reason = "invalid_json"
                logger.warning("LLM parse failed; using rule fallback: %s", exc)
            except LLMError as exc:
                llm_ms = _elapsed_ms(t_llm)
                fallback_reason = "llm_error"
                logger.warning("LLM call failed; using rule fallback: %s", exc)
            else:
                llm_ms = _elapsed_ms(t_llm)
                t_assemble = time.perf_counter()
                items = assemble_from_llm(result.frame, prefs, parsed, settings)
                summary = (parsed.summary or "").strip() or _fallback_summary(prefs, len(items))
                assemble_ms = _elapsed_ms(t_assemble)

            if source != "llm":
                t_assemble = time.perf_counter()
                items = assemble_items(result.frame, prefs, source="fallback")
                summary = _fallback_summary(prefs, len(items))
                assemble_ms = _elapsed_ms(t_assemble)

    latency_ms = _elapsed_ms(started)
    suggestions: List[str] = []
    if empty:
        logger.info(
            "empty_result location=%s cuisine=%s budget=%s min_rating=%s stages=%s",
            prefs.location,
            prefs.cuisines,
            prefs.budget,
            prefs.min_rating,
            result.stage_counts,
        )
        source = "fallback"
        fallback_reason = None
        items = []
        summary = None
        suggestions = empty_suggestions(prefs, result.stage_counts, result.relaxations_applied)

    breakdown = LatencyBreakdown(
        normalize_ms=normalize_ms,
        filter_ms=filter_ms,
        llm_ms=llm_ms,
        assemble_ms=assemble_ms,
        total_ms=latency_ms,
    )
    meta = RecommendMeta(
        candidates_considered=result.candidates_considered,
        filters_applied=result.filters_applied,
        relaxations_applied=result.relaxations_applied,
        source=source,
        latency_ms=latency_ms,
        empty_reason="no_restaurants_matched" if empty else None,
        suggestions=suggestions,
        llm_model=settings.resolved_llm_model() if source == "llm" else None,
        fallback_reason=fallback_reason if not empty else None,
        request_id=rid,
        cache_hit=False,
        filter_stage_counts=dict(result.stage_counts),
        latency_breakdown=breakdown,
    )
    response = RecommendResponse(summary=summary, recommendations=items, meta=meta)
    cache.set(cache_key, response)
    metrics.record(
        source=source,
        empty=empty,
        fallback_reason=fallback_reason if not empty else None,
        relaxations=result.relaxations_applied,
        cache_hit=False,
    )
    logger.info(
        "recommend request_id=%s source=%s empty=%s fallback_reason=%s location=%s "
        "cuisine=%s candidates=%s filter_ms=%s llm_ms=%s total_ms=%s relaxations=%s stages=%s",
        rid,
        source,
        empty,
        fallback_reason,
        prefs.location,
        prefs.cuisines,
        result.candidates_considered,
        filter_ms,
        llm_ms,
        latency_ms,
        result.relaxations_applied,
        result.stage_counts,
    )
    return response
