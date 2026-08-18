"""Parse LLM JSON, repair lightly, and ground ids to the candidate catalog."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from typing import Any, Iterable, List, Sequence, Set

from src.llm.exceptions import LLMParseError

_FENCE_RE = re.compile(r"```(?:json)?\s*(.*?)\s*```", re.DOTALL | re.IGNORECASE)
_TRAILING_COMMA_RE = re.compile(r",(\s*[}\]])")


@dataclass
class LLMPick:
    id: str
    rank: int
    explanation: str
    fit_notes: List[str] = field(default_factory=list)


@dataclass
class ParsedLLMOutput:
    summary: str
    picks: List[LLMPick]
    dropped_ids: List[str] = field(default_factory=list)


def extract_json_text(raw: str) -> str:
    text = (raw or "").strip()
    if not text:
        raise LLMParseError("empty model output")
    fenced = _FENCE_RE.search(text)
    if fenced:
        text = fenced.group(1).strip()
    start = text.find("{")
    end = text.rfind("}")
    if start == -1 or end == -1 or end <= start:
        raise LLMParseError("no JSON object found")
    return text[start : end + 1]


def repair_json_text(text: str) -> str:
    return _TRAILING_COMMA_RE.sub(r"\1", text)


def _load_object(raw: str) -> Dict[str, Any]:
    blob = extract_json_text(raw)
    try:
        payload = json.loads(blob)
    except json.JSONDecodeError:
        payload = json.loads(repair_json_text(blob))
    if not isinstance(payload, dict):
        raise LLMParseError("JSON root is not an object")
    return payload


def _as_notes(value: Any) -> List[str]:
    if value is None:
        return []
    if isinstance(value, str):
        text = value.strip()
        return [text] if text else []
    if isinstance(value, Sequence) and not isinstance(value, (bytes, bytearray)):
        notes = []
        for item in value:
            text = str(item).strip()
            if text:
                notes.append(text)
        return notes
    return []


def parse_llm_json(raw: str) -> ParsedLLMOutput:
    try:
        payload = _load_object(raw)
    except (json.JSONDecodeError, LLMParseError) as exc:
        raise LLMParseError("invalid JSON from model") from exc

    summary = str(payload.get("summary") or "").strip()
    recs = payload.get("recommendations")
    if recs is None:
        recs = payload.get("results") or payload.get("picks") or []
    if not isinstance(recs, list):
        raise LLMParseError("recommendations is not a list")

    picks: List[LLMPick] = []
    for index, item in enumerate(recs):
        if not isinstance(item, dict):
            continue
        rest_id = str(item.get("id") or "").strip()
        if not rest_id:
            continue
        rank_raw = item.get("rank", index + 1)
        try:
            rank = int(rank_raw)
        except (TypeError, ValueError):
            rank = index + 1
        explanation = str(item.get("explanation") or item.get("reason") or "").strip()
        picks.append(
            LLMPick(
                id=rest_id,
                rank=rank,
                explanation=explanation,
                fit_notes=_as_notes(item.get("fit_notes")),
            )
        )
    if not picks:
        raise LLMParseError("no recommendations in model output")
    picks.sort(key=lambda pick: (pick.rank, pick.id))
    return ParsedLLMOutput(summary=summary, picks=picks)


def ground_picks(
    parsed: ParsedLLMOutput,
    allowed_ids: Iterable[str],
    *,
    top_k: int,
) -> ParsedLLMOutput:
    allowed: Set[str] = {str(item) for item in allowed_ids}
    seen: Set[str] = set()
    kept: List[LLMPick] = []
    dropped: List[str] = []
    for pick in parsed.picks:
        if pick.id not in allowed:
            dropped.append(pick.id)
            continue
        if pick.id in seen:
            continue
        seen.add(pick.id)
        kept.append(pick)
        if len(kept) >= top_k:
            break
    if not kept:
        raise LLMParseError("no grounded restaurant ids")
    for index, pick in enumerate(kept, start=1):
        pick.rank = index
    return ParsedLLMOutput(summary=parsed.summary, picks=kept, dropped_ids=dropped)


def parse_and_ground(raw: str, allowed_ids: Iterable[str], *, top_k: int) -> ParsedLLMOutput:
    return ground_picks(parse_llm_json(raw), allowed_ids, top_k=top_k)
