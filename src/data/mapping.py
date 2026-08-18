"""Source (Hugging Face Zomato CSV) → canonical field mapping.

The Bangalore Zomato dump uses locality in `location` and listing-area in
`listed_in(city)`. All rows are Bangalore; `city` is set to that constant so
sample queries like "Bangalore" match.
"""

from __future__ import annotations

SOURCE_REQUIRED_COLUMNS = (
    "name",
    "location",
    "cuisines",
    "rate",
    "approx_cost(for two people)",
)

# Loaded from the CSV / HF dataset. Heavy text dumps are omitted on purpose.
SOURCE_LOAD_COLUMNS = (
    "url",
    "address",
    "name",
    "online_order",
    "book_table",
    "rate",
    "votes",
    "location",
    "rest_type",
    "cuisines",
    "approx_cost(for two people)",
    "listed_in(city)",
)

DATASET_CITY = "Bangalore"


class SchemaMappingError(ValueError):
    """Raised when the source table is missing expected columns."""


def assert_source_columns(columns) -> None:
    present = set(columns)
    missing = [c for c in SOURCE_REQUIRED_COLUMNS if c not in present]
    if missing:
        raise SchemaMappingError(
            "Hugging Face dataset schema differs from assumptions. "
            "Missing required columns: {missing}. Present: {present}".format(
                missing=missing,
                present=sorted(present),
            )
        )
