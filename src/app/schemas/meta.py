"""GET /meta/filters contract for UI dropdowns."""

from __future__ import annotations

from typing import List, Optional

from pydantic import BaseModel, Field


class BudgetBounds(BaseModel):
    low_max: float
    medium_max: float
    unit: str = "INR approximate cost for two"


class FilterMetaResponse(BaseModel):
    cities: List[str] = Field(default_factory=list, description="Catalog city values (not used for Neighborhood).")
    locations: List[str] = Field(
        default_factory=list,
        description="Neighbourhoods from the catalog location column, ranked by restaurant count.",
    )
    cuisines: List[str] = Field(default_factory=list)
    budget_bands: List[str] = Field(default_factory=lambda: ["low", "medium", "high"])
    budget_bounds: BudgetBounds
    min_rating_default: float
    rating_range: List[float] = Field(default_factory=lambda: [0.0, 5.0])
    top_k_default: int
    top_k_range: List[int] = Field(default_factory=lambda: [1, 10])
    additional_preference_hints: List[str] = Field(default_factory=list)
    default_location: Optional[str] = None
    catalog_rows: int = 0
