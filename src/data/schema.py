"""Canonical schema version and column contracts."""

from __future__ import annotations

# Bump when mapping or derived-field logic changes so stale caches are rebuilt.
CACHE_SCHEMA_VERSION = "v1"

CANONICAL_COLUMNS = (
    "id",
    "name",
    "location",
    "city",
    "cuisine",
    "rating",
    "cost_for_two",
    "budget_band",
    "votes",
    "rest_type",
    "online_order",
    "book_table",
    "address",
    "search_document",
)

REQUIRED_CANONICAL = ("id", "name", "location", "cuisine", "rating", "cost_for_two")
