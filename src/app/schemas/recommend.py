"""Request/response contracts for POST /recommend."""

from __future__ import annotations

from typing import Dict, List, Literal, Optional

from pydantic import BaseModel, Field

from src.config import get_settings


def _defaults():
    return get_settings()


class RecommendRequest(BaseModel):
    location: str = Field(..., min_length=1, description="City or locality")
    budget: Literal["low", "medium", "high"]
    cuisine: List[str] = Field(default_factory=list)
    min_rating: float = Field(default_factory=lambda: _defaults().min_rating_default, ge=0, le=5)
    additional_preferences: str = Field(
        default="",
        max_length=500,
        description="Free-text extras such as family-friendly or quick service",
    )
    top_k: int = Field(default_factory=lambda: _defaults().default_top_k, ge=1, le=10)


class RecommendationItem(BaseModel):
    rank: int
    id: str
    name: str
    cuisine: str
    rating: Optional[float] = None
    estimated_cost: Optional[float] = None
    location: str
    explanation: str
    match_score: float
    source: str = "fallback"
    fit_notes: List[str] = Field(default_factory=list)


class LatencyBreakdown(BaseModel):
    normalize_ms: int = 0
    filter_ms: int = 0
    llm_ms: int = 0
    assemble_ms: int = 0
    total_ms: int = 0


class RecommendMeta(BaseModel):
    candidates_considered: int
    filters_applied: List[str]
    relaxations_applied: List[str] = Field(default_factory=list)
    source: str = "fallback"
    latency_ms: Optional[int] = None
    empty_reason: Optional[str] = None
    suggestions: List[str] = Field(default_factory=list)
    llm_model: Optional[str] = None
    fallback_reason: Optional[str] = None
    request_id: Optional[str] = None
    cache_hit: bool = False
    filter_stage_counts: Dict[str, int] = Field(default_factory=dict)
    latency_breakdown: Optional[LatencyBreakdown] = None


class RecommendResponse(BaseModel):
    summary: Optional[str] = None
    recommendations: List[RecommendationItem]
    meta: RecommendMeta
