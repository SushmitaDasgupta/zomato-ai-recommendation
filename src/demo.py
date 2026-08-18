"""Fixed demo walkthrough requests (Phase 3)."""

from __future__ import annotations

import argparse
import json
import logging
import sys
from typing import Any, Dict, List, Optional

from src.app.schemas.recommend import RecommendRequest
from src.config import get_settings
from src.data.catalog import Catalog
from src.data.ingest import CatalogCacheError
from src.engine.recommend import recommend
from src.observability import configure_logging

logger = logging.getLogger(__name__)

SCENARIOS: List[Dict[str, Any]] = [
    {
        "id": "bangalore-italian-medium",
        "title": "Bangalore Italian, medium budget",
        "request": {
            "location": "Bangalore",
            "budget": "medium",
            "cuisine": ["Italian"],
            "min_rating": 4.0,
            "additional_preferences": "family-friendly",
            "top_k": 5,
        },
        "notes": "Happy-path walkthrough from the problem statement.",
    },
    {
        "id": "multi-cuisine",
        "title": "Italian + Chinese night out",
        "request": {
            "location": "Bangalore",
            "budget": "medium",
            "cuisine": ["Italian", "Chinese"],
            "min_rating": 3.5,
            "additional_preferences": "casual",
            "top_k": 5,
        },
        "notes": "Multi-cuisine OR match — expect a mix, not only the first cuisine.",
    },
    {
        "id": "free-text-extras",
        "title": "Soft prefs only (rooftop / romantic)",
        "request": {
            "location": "Bangalore",
            "budget": "high",
            "cuisine": [],
            "min_rating": 4.0,
            "additional_preferences": "romantic rooftop fine dining",
            "top_k": 5,
        },
        "notes": "Keywords boost ranking; they never act as hard filters.",
    },
    {
        "id": "few-matches-locality",
        "title": "Indiranagar Italian (few matches)",
        "request": {
            "location": "Indiranagar",
            "budget": "medium",
            "cuisine": ["Italian"],
            "min_rating": 4.0,
            "additional_preferences": "",
            "top_k": 5,
        },
        "notes": "Narrow locality — small list or adjacent-budget relaxation.",
    },
    {
        "id": "empty-impossible",
        "title": "Impossible filters (empty state)",
        "request": {
            "location": "Atlantis",
            "budget": "low",
            "cuisine": ["Martian"],
            "min_rating": 4.9,
            "additional_preferences": "",
            "top_k": 5,
        },
        "notes": "Must return an empty list plus tips to relax location/rating/budget.",
        "expect_empty": True,
    },
]


def scenario_by_id(scenario_id: str) -> Dict[str, Any]:
    for item in SCENARIOS:
        if item["id"] == scenario_id:
            return item
    raise KeyError("Unknown demo scenario: {0}".format(scenario_id))


def run_scenario(
    scenario: Dict[str, Any],
    *,
    catalog: Catalog,
    settings=None,
    llm_client=None,
):
    body = RecommendRequest(**scenario["request"])
    return recommend(body, catalog=catalog, settings=settings, llm_client=llm_client)


def _print_result(scenario: Dict[str, Any], result) -> None:
    meta = result.meta
    print("=== {0} ({1}) ===".format(scenario["title"], scenario["id"]))
    print(scenario["notes"])
    print(
        "source={source} empty={empty} fallback={reason} candidates={c} "
        "filter_ms={f} llm_ms={l} total_ms={t} relaxations={rel}".format(
            source=meta.source,
            empty=not result.recommendations,
            reason=meta.fallback_reason,
            c=meta.candidates_considered,
            f=(meta.latency_breakdown.filter_ms if meta.latency_breakdown else "—"),
            l=(meta.latency_breakdown.llm_ms if meta.latency_breakdown else "—"),
            t=meta.latency_ms,
            rel=meta.relaxations_applied,
        )
    )
    if result.summary:
        print("summary: {0}".format(result.summary))
    if not result.recommendations:
        print("No matches.")
        for tip in meta.suggestions:
            print("  - {0}".format(tip))
        print()
        return
    for item in result.recommendations:
        print(
            "{rank}. {name}  rating={rating}  cost={cost}  {location}".format(
                rank=item.rank,
                name=item.name,
                rating=item.rating if item.rating is not None else "N/A",
                cost=item.estimated_cost if item.estimated_cost is not None else "N/A",
                location=item.location,
            )
        )
        print("   {0}".format(item.explanation))
    print()


def main(argv: Optional[list] = None) -> int:
    settings = get_settings()
    configure_logging(settings)
    parser = argparse.ArgumentParser(description="Run fixed recommendation demo scenarios.")
    parser.add_argument("--scenario", help="Run a single scenario id")
    parser.add_argument("--json", action="store_true", help="Print JSON instead of text")
    parser.add_argument("--list", action="store_true", help="List scenario ids and exit")
    args = parser.parse_args(argv)

    if args.list:
        for item in SCENARIOS:
            print("{0}\t{1}".format(item["id"], item["title"]))
        return 0

    try:
        catalog = Catalog.load()
    except CatalogCacheError as exc:
        print(str(exc), file=sys.stderr)
        print("Setup: python -m src.data.ingest", file=sys.stderr)
        return 1

    selected = [scenario_by_id(args.scenario)] if args.scenario else SCENARIOS
    payloads = []
    for scenario in selected:
        result = run_scenario(scenario, catalog=catalog, settings=settings)
        if args.json:
            payloads.append(
                {
                    "id": scenario["id"],
                    "title": scenario["title"],
                    "result": result.model_dump(),
                }
            )
        else:
            _print_result(scenario, result)

    if args.json:
        print(json.dumps(payloads, indent=2, default=str))
    return 0


if __name__ == "__main__":
    sys.exit(main())
