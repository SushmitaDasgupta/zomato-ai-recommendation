"""Request IDs, counters, TTL cache, and recommend logs (architecture §11)."""

from __future__ import annotations

import hashlib
import json
import logging
import threading
import time
from collections import Counter
from contextvars import ContextVar
from typing import Any, Optional
from uuid import uuid4

from src.config import Settings, get_settings

logger = logging.getLogger(__name__)

request_id_var: ContextVar[str] = ContextVar("request_id", default="-")


class _RequestIdFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        record.request_id = request_id_var.get("-")
        return True


def new_request_id() -> str:
    return uuid4().hex[:12]


def set_request_id(value: Optional[str] = None) -> str:
    rid = str(value or "").strip() or new_request_id()
    request_id_var.set(rid)
    return rid


def get_request_id() -> str:
    return request_id_var.get("-")


class RecommendMetrics:
    def __init__(self) -> None:
        self._lock = threading.Lock()
        self.recommend_total = 0
        self.recommend_llm = 0
        self.recommend_fallback = 0
        self.recommend_empty = 0
        self.cache_hits = 0
        self.relaxations: Counter = Counter()
        self.fallback_reasons: Counter = Counter()

    def reset(self) -> None:
        with self._lock:
            self.recommend_total = 0
            self.recommend_llm = 0
            self.recommend_fallback = 0
            self.recommend_empty = 0
            self.cache_hits = 0
            self.relaxations.clear()
            self.fallback_reasons.clear()

    def record(
        self,
        *,
        source: str,
        empty: bool,
        fallback_reason: Optional[str],
        relaxations: Optional[list] = None,
        cache_hit: bool = False,
    ) -> None:
        with self._lock:
            self.recommend_total += 1
            if cache_hit:
                self.cache_hits += 1
            if empty:
                self.recommend_empty += 1
            elif source == "llm":
                self.recommend_llm += 1
            else:
                self.recommend_fallback += 1
            for item in relaxations or []:
                self.relaxations[str(item)] += 1
            if fallback_reason:
                self.fallback_reasons[str(fallback_reason)] += 1

    def snapshot(self) -> dict:
        with self._lock:
            non_empty = self.recommend_total - self.recommend_empty
            return {
                "recommend_total": self.recommend_total,
                "recommend_llm": self.recommend_llm,
                "recommend_fallback": self.recommend_fallback,
                "recommend_empty": self.recommend_empty,
                "cache_hits": self.cache_hits,
                "empty_rate": round(self.recommend_empty / self.recommend_total, 4) if self.recommend_total else 0.0,
                "fallback_rate": round(self.recommend_fallback / non_empty, 4) if non_empty else 0.0,
                "relaxations": dict(self.relaxations),
                "fallback_reasons": dict(self.fallback_reasons),
            }


metrics = RecommendMetrics()

_logging_configured = False


def configure_logging(settings: Optional[Settings] = None) -> None:
    global _logging_configured
    settings = settings or get_settings()
    level = getattr(logging, str(settings.log_level).upper(), logging.INFO)
    if not _logging_configured:
        logging.basicConfig(
            level=level,
            format="%(asctime)s %(levelname)s [%(request_id)s] %(name)s: %(message)s",
        )
        rid_filter = _RequestIdFilter()
        root = logging.getLogger()
        root.addFilter(rid_filter)
        for handler in root.handlers:
            handler.addFilter(rid_filter)
            handler.setLevel(level)
        _logging_configured = True
    else:
        logging.getLogger().setLevel(level)


class TtlCache:
    """Process-local dict with a short TTL (optional Phase 3 stretch)."""

    def __init__(self, ttl_seconds: float, maxsize: int = 128) -> None:
        self.ttl_seconds = float(ttl_seconds)
        self.maxsize = max(1, int(maxsize))
        self._data: dict[str, tuple[float, Any]] = {}
        self._lock = threading.Lock()

    def enabled(self) -> bool:
        return self.ttl_seconds > 0

    def get(self, key: str) -> Optional[Any]:
        if not self.enabled():
            return None
        now = time.monotonic()
        with self._lock:
            item = self._data.get(key)
            if item is None:
                return None
            expires, value = item
            if expires <= now:
                self._data.pop(key, None)
                return None
            return value

    def set(self, key: str, value: Any) -> None:
        if not self.enabled():
            return
        expires = time.monotonic() + self.ttl_seconds
        with self._lock:
            if key not in self._data and len(self._data) >= self.maxsize:
                oldest_key = min(self._data, key=lambda name: self._data[name][0])
                self._data.pop(oldest_key, None)
            self._data[key] = (expires, value)


_recommend_cache: Optional[TtlCache] = None
_recommend_cache_ttl: Optional[float] = None


def reset_recommend_cache() -> None:
    global _recommend_cache, _recommend_cache_ttl
    _recommend_cache = None
    _recommend_cache_ttl = None


def recommend_cache(settings: Optional[Settings] = None) -> TtlCache:
    global _recommend_cache, _recommend_cache_ttl
    settings = settings or get_settings()
    ttl = float(settings.recommend_cache_ttl_seconds)
    if _recommend_cache is None or _recommend_cache_ttl != ttl:
        _recommend_cache = TtlCache(ttl, maxsize=settings.recommend_cache_maxsize)
        _recommend_cache_ttl = ttl
    return _recommend_cache


def preference_cache_key(prefs: Any) -> str:
    payload = {
        "location": str(getattr(prefs, "location", "")).casefold(),
        "budget": getattr(prefs, "budget", ""),
        "cuisines": list(getattr(prefs, "cuisines", []) or []),
        "min_rating": getattr(prefs, "min_rating", None),
        "additional": str(getattr(prefs, "additional_preferences", "")).casefold(),
        "top_k": getattr(prefs, "top_k", None),
    }
    blob = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(blob.encode("utf-8")).hexdigest()
