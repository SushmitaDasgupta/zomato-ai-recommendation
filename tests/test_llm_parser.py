"""Parser: JSON repair, grounding, hallucinated ids dropped."""

from __future__ import annotations

import pytest

from src.llm.exceptions import LLMParseError
from src.llm.parser import ground_picks, parse_and_ground, parse_llm_json


GOLDEN = """
{
  "summary": "Best Italian fits nearby.",
  "recommendations": [
    {"id": "r-keep", "rank": 2, "explanation": "Fits budget.", "fit_notes": ["budget"]},
    {"id": "r-first", "rank": 1, "explanation": "Top cuisine match.", "fit_notes": ["cuisine"]}
  ]
}
"""


def test_parse_golden_json_orders_by_rank():
    parsed = parse_llm_json(GOLDEN)
    assert parsed.summary.startswith("Best Italian")
    assert [pick.id for pick in parsed.picks] == ["r-first", "r-keep"]
    assert parsed.picks[0].explanation == "Top cuisine match."


def test_parse_strips_markdown_fence_and_trailing_comma():
    raw = """```json
    {
      "summary": "ok",
      "recommendations": [
        {"id": "r-1", "rank": 1, "explanation": "yes",},
      ],
    }
    ```"""
    parsed = parse_llm_json(raw)
    assert parsed.picks[0].id == "r-1"


def test_hallucinated_id_dropped():
    parsed = parse_llm_json(
        '{"summary": "s", "recommendations": ['
        '{"id": "r-real", "rank": 1, "explanation": "real"},'
        '{"id": "r-ghost", "rank": 2, "explanation": "invented"}'
        "]}"
    )
    grounded = ground_picks(parsed, ["r-real"], top_k=5)
    assert [pick.id for pick in grounded.picks] == ["r-real"]
    assert grounded.dropped_ids == ["r-ghost"]
    assert grounded.picks[0].rank == 1


def test_all_hallucinated_ids_fail():
    with pytest.raises(LLMParseError):
        parse_and_ground(
            '{"summary": "s", "recommendations": [{"id": "r-ghost", "rank": 1, "explanation": "x"}]}',
            ["r-real"],
            top_k=5,
        )


def test_empty_or_non_json_fails():
    with pytest.raises(LLMParseError):
        parse_llm_json("")
    with pytest.raises(LLMParseError):
        parse_llm_json("sorry, here are some restaurants")
