"use client";

import { useEffect, useState } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { EmptyCanvas } from "@/components/preference-form/EmptyCanvas";
import { PreferenceForm } from "@/components/preference-form/PreferenceForm";
import { getFilters } from "@/lib/api";
import {
  DEMO_PRESET,
  EMPTY_FORM,
  parsePreferences,
  resultsHref,
} from "@/lib/preferences";
import type { FilterMetaResponse, PreferenceFormState } from "@/lib/types";

export function FindTableView() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const [form, setForm] = useState<PreferenceFormState>(
    () => parsePreferences(searchParams) ?? EMPTY_FORM,
  );
  const [filters, setFilters] = useState<FilterMetaResponse | null>(null);
  const [filtersError, setFiltersError] = useState(false);
  const [submitting, setSubmitting] = useState(false);

  const query = searchParams.toString();

  useEffect(() => {
    const fromUrl = parsePreferences(new URLSearchParams(query));
    let cancelled = false;
    getFilters()
      .then((meta) => {
        if (cancelled) {
          return;
        }
        setFilters(meta);
        setForm((current) => {
          if (fromUrl) {
            return { ...fromUrl, top_k: fromUrl.top_k || meta.top_k_default || 5 };
          }
          if (current.location) {
            return current;
          }
          return {
            ...EMPTY_FORM,
            location: meta.default_location || "",
            min_rating: meta.min_rating_default ?? 3.5,
            top_k: meta.top_k_default ?? 5,
          };
        });
      })
      .catch(() => {
        if (cancelled) {
          return;
        }
        setFiltersError(true);
        if (fromUrl) {
          setForm(fromUrl);
        } else {
          setForm((current) => (current.location ? current : EMPTY_FORM));
        }
      });
    return () => {
      cancelled = true;
    };
  }, [query]);

  function submit(next: PreferenceFormState = form) {
    if (!next.location.trim()) {
      return;
    }
    setSubmitting(true);
    router.push(resultsHref(next));
  }

  return (
    <>
      <PreferenceForm
        value={form}
        onChange={setForm}
        onSubmit={() => submit()}
        submitting={submitting}
        filters={filters}
        filtersError={filtersError}
      />
      <EmptyCanvas
        onApplyPreset={() => {
          const preset = {
            ...DEMO_PRESET,
            min_rating: filters?.min_rating_default ? 4 : DEMO_PRESET.min_rating,
            top_k: filters?.top_k_default ?? DEMO_PRESET.top_k,
          };
          setForm(preset);
        }}
      />
    </>
  );
}
