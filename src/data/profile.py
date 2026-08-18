"""Print catalog coverage stats (Phase 0 data profile)."""

from __future__ import annotations

import argparse
import logging
from pathlib import Path
from typing import Optional

from src.config import get_settings
from src.data.catalog import Catalog


def profile(cache_dir: Optional[Path] = None, sample_n: int = 5) -> None:
    catalog = Catalog.load(cache_dir=cache_dir)
    df = catalog.frame
    print("rows: {0}".format(len(df)))
    print("distinct locations: {0}".format(len(catalog.list_locations())))
    print("distinct cuisines: {0}".format(len(catalog.list_cuisines())))
    print("null rating: {0}".format(int(df["rating"].isna().sum())))
    print("null cost_for_two: {0}".format(int(df["cost_for_two"].isna().sum())))
    print("budget_band counts:")
    print(df["budget_band"].value_counts(dropna=False).to_string())
    bangalore = catalog.query("Bangalore")
    print("Bangalore matches: {0}".format(len(bangalore)))
    print("sample restaurants:")
    cols = [c for c in ("name", "location", "city", "cuisine", "rating", "cost_for_two", "budget_band") if c in df.columns]
    print(df[cols].head(sample_n).to_string(index=False))


def main(argv: Optional[list] = None) -> None:
    logging.basicConfig(level=get_settings().log_level.upper(), format="%(levelname)s %(message)s")
    parser = argparse.ArgumentParser(description="Profile the processed restaurant catalog.")
    parser.add_argument("--sample", type=int, default=5)
    args = parser.parse_args(argv)
    profile(sample_n=args.sample)


if __name__ == "__main__":
    main()
