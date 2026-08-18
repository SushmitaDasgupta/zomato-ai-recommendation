"use client";

import { useEffect, useMemo, useState } from "react";
import type { BudgetBand, FilterMetaResponse, PreferenceFormState } from "@/lib/types";
import {
  FALLBACK_CUISINES,
  VIBE_CHIPS,
  appendVibe,
  featuredCuisines,
} from "@/lib/preferences";
import { Button } from "@/components/ui/Button";
import { Chip } from "@/components/ui/Chip";
import { Icon } from "@/components/ui/Icon";
import { Input } from "@/components/ui/Input";
import { SegmentedControl } from "@/components/ui/SegmentedControl";
import { Slider } from "@/components/ui/Slider";

const BUDGET_OPTIONS: { value: BudgetBand; label: string }[] = [
  { value: "low", label: "Low" },
  { value: "medium", label: "Medium" },
  { value: "high", label: "High" },
];

interface PreferenceFormProps {
  value: PreferenceFormState;
  onChange: (next: PreferenceFormState) => void;
  onSubmit: () => void;
  submitting?: boolean;
  filters: FilterMetaResponse | null;
  filtersError?: boolean;
}

export function PreferenceForm({
  value,
  onChange,
  onSubmit,
  submitting = false,
  filters,
  filtersError = false,
}: PreferenceFormProps) {
  const [locationQuery, setLocationQuery] = useState(value.location);
  const [showSuggestions, setShowSuggestions] = useState(false);
  const [cuisineQuery, setCuisineQuery] = useState("");

  useEffect(() => {
    setLocationQuery(value.location);
  }, [value.location]);

  const locations = useMemo(() => filters?.locations ?? [], [filters]);

  const cuisineOptions = useMemo(() => {
    const catalog = filters?.cuisines ?? [];
    const featured = featuredCuisines(catalog.length ? catalog : FALLBACK_CUISINES);
    const extra = value.cuisine.filter(
      (item) => !featured.some((f) => f.toLowerCase() === item.toLowerCase()),
    );
    return [...featured, ...extra];
  }, [filters, value.cuisine]);

  const visibleCuisines = useMemo(() => {
    const q = cuisineQuery.trim().toLowerCase();
    if (!q) {
      return cuisineOptions.slice(0, 12);
    }
    const pool = filters?.cuisines?.length ? filters.cuisines : cuisineOptions;
    return pool.filter((item) => item.toLowerCase().includes(q)).slice(0, 12);
  }, [cuisineOptions, cuisineQuery, filters]);

  const locationMatches = useMemo(() => {
    const q = locationQuery.trim().toLowerCase();
    if (!q) {
      return locations.slice(0, 8);
    }
    return locations.filter((item) => item.toLowerCase().includes(q)).slice(0, 8);
  }, [locationQuery, locations]);

  const vibeHints = filters?.additional_preference_hints?.length
    ? filters.additional_preference_hints.slice(0, 6)
    : [...VIBE_CHIPS];

  function patch(partial: Partial<PreferenceFormState>) {
    onChange({ ...value, ...partial });
  }

  function toggleCuisine(name: string) {
    const exists = value.cuisine.some((item) => item.toLowerCase() === name.toLowerCase());
    patch({
      cuisine: exists
        ? value.cuisine.filter((item) => item.toLowerCase() !== name.toLowerCase())
        : [...value.cuisine, name],
    });
  }

  return (
    <aside className="z-30 flex h-auto w-full shrink-0 flex-col overflow-y-auto border-r border-outline-variant bg-level-1 md:h-full md:w-[380px]">
      <form
        className="flex flex-1 flex-col"
        onSubmit={(event) => {
          event.preventDefault();
          onSubmit();
        }}
      >
        <div className="flex flex-1 flex-col gap-lg p-md">
          <div>
            <label
              htmlFor="neighborhood"
              className="mb-2 block font-geist text-label-sm uppercase tracking-wider text-on-surface-variant"
            >
              Neighborhood
            </label>
            <div className="relative">
              <Input
                id="neighborhood"
                name="location"
                autoComplete="off"
                placeholder="Search localities..."
                value={locationQuery}
                leading={<Icon name="location_on" className="text-[20px]" />}
                onFocus={() => setShowSuggestions(true)}
                onBlur={() => {
                  window.setTimeout(() => setShowSuggestions(false), 120);
                }}
                onChange={(event) => {
                  const next = event.target.value;
                  setLocationQuery(next);
                  patch({ location: next });
                }}
              />
              {showSuggestions && locationMatches.length > 0 ? (
                <ul
                  role="listbox"
                  className="absolute z-20 mt-1 max-h-48 w-full overflow-y-auto rounded-md border border-outline-variant bg-level-1"
                >
                  {locationMatches.map((item) => (
                    <li key={item}>
                      <button
                        type="button"
                        className="w-full px-3 py-2 text-left font-geist text-body-md text-on-surface hover:bg-surface-container"
                        onMouseDown={(event) => event.preventDefault()}
                        onClick={() => {
                          setLocationQuery(item);
                          patch({ location: item });
                          setShowSuggestions(false);
                        }}
                      >
                        {item}
                      </button>
                    </li>
                  ))}
                </ul>
              ) : null}
            </div>
            {filtersError ? (
              <p className="mt-2 font-geist text-label-sm text-on-surface-variant">
                Catalog dropdowns unavailable — type a locality instead.
              </p>
            ) : null}
          </div>

          <div>
            <span
              id="budget-label"
              className="mb-2 block font-geist text-label-sm uppercase tracking-wider text-on-surface-variant"
            >
              Budget Level
            </span>
            <SegmentedControl
              name="budget"
              aria-labelledby="budget-label"
              value={value.budget}
              options={BUDGET_OPTIONS}
              onChange={(budget) => patch({ budget })}
            />
          </div>

          <div>
            <span className="mb-2 block font-geist text-label-sm uppercase tracking-wider text-on-surface-variant">
              Cuisine Focus
            </span>
            {filters?.cuisines && filters.cuisines.length > 12 ? (
              <Input
                className="mb-2 bg-level-0"
                placeholder="Filter cuisines..."
                value={cuisineQuery}
                onChange={(event) => setCuisineQuery(event.target.value)}
                aria-label="Filter cuisines"
              />
            ) : null}
            <div className="flex flex-wrap gap-2">
              {visibleCuisines.map((name) => (
                <Chip
                  key={name}
                  selected={value.cuisine.some((item) => item.toLowerCase() === name.toLowerCase())}
                  onClick={() => toggleCuisine(name)}
                  aria-pressed={value.cuisine.some((item) => item.toLowerCase() === name.toLowerCase())}
                >
                  {name}
                </Chip>
              ))}
            </div>
          </div>

          <div>
            <div className="mb-2 flex justify-between">
              <label
                id="rating-label"
                htmlFor="min-rating"
                className="block font-geist text-label-sm uppercase tracking-wider text-on-surface-variant"
              >
                Minimum Rating
              </label>
              <span className="font-geist text-label-sm text-secondary">{value.min_rating.toFixed(1)}+</span>
            </div>
            <Slider
              id="min-rating"
              min={1}
              max={5}
              step={0.1}
              value={value.min_rating}
              aria-labelledby="rating-label"
              onChange={(min_rating) => patch({ min_rating: Number(min_rating.toFixed(1)) })}
            />
          </div>

          <div>
            <label
              htmlFor="vibe"
              className="mb-2 block font-geist text-label-sm uppercase tracking-wider text-on-surface-variant"
            >
              Vibe &amp; Intent (Optional)
            </label>
            <textarea
              id="vibe"
              name="additional_preferences"
              placeholder="Describe what you're looking for..."
              value={value.additional_preferences}
              onChange={(event) => patch({ additional_preferences: event.target.value })}
              maxLength={500}
              className="h-24 w-full resize-none rounded-md border border-outline-variant bg-level-0 p-3 font-geist text-body-md text-on-surface placeholder:text-surface-variant focus-tomato"
            />
            <div className="mt-2 flex flex-wrap gap-2">
              {vibeHints.map((chip) => (
                <Chip
                  key={chip}
                  tone="gold"
                  className="rounded-full px-2 py-0.5 text-xs"
                  onClick={() => patch({ additional_preferences: appendVibe(value.additional_preferences, chip) })}
                >
                  + {chip}
                </Chip>
              ))}
            </div>
          </div>
        </div>

        <div className="border-t border-outline-variant bg-level-1 p-md">
          <Button type="submit" className="w-full py-3" disabled={submitting || !value.location.trim()}>
            <Icon name="auto_awesome" className="text-[18px]" />
            {submitting ? "Finding tables…" : "Get recommendations"}
          </Button>
        </div>
      </form>
    </aside>
  );
}
