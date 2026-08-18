"use client";

import Link from "next/link";
import { useCallback, useEffect, useState } from "react";
import { useSearchParams } from "next/navigation";
import { EmptyResults } from "@/components/results/EmptyResults";
import { ErrorBanner } from "@/components/results/ErrorBanner";
import { RequestSummary } from "@/components/results/RequestSummary";
import { RestaurantHeroCard } from "@/components/results/RestaurantHeroCard";
import { RestaurantRowCard } from "@/components/results/RestaurantRowCard";
import { ResultsFooter } from "@/components/results/ResultsFooter";
import { SkeletonResults } from "@/components/results/SkeletonResults";
import { SummaryBanner } from "@/components/results/SummaryBanner";
import { Button } from "@/components/ui/Button";
import { ApiError, recommend } from "@/lib/api";
import { parsePreferences, toRecommendRequest } from "@/lib/preferences";
import type { PreferenceFormState, RecommendResponse } from "@/lib/types";

export function ResultsView() {
  const searchParams = useSearchParams();
  const request = parsePreferences(searchParams);
  const [data, setData] = useState<RecommendResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(Boolean(request));

  const load = useCallback(async (prefs: PreferenceFormState) => {
    setLoading(true);
    setError(null);
    try {
      const result = await recommend(toRecommendRequest(prefs));
      setData(result);
    } catch (err) {
      const message =
        err instanceof ApiError
          ? err.message
          : process.env.NODE_ENV === "production"
            ? "Could not reach the recommendation API. Try again in a moment."
            : "Could not reach the recommendation API. Is uvicorn running on port 8000?";
      setError(message);
      setData(null);
    } finally {
      setLoading(false);
    }
  }, []);

  const query = searchParams.toString();

  useEffect(() => {
    const prefs = parsePreferences(new URLSearchParams(query));
    if (!prefs) {
      return;
    }
    void load(prefs);
  }, [load, query]);

  if (!request) {
    return (
      <main className="flex flex-1 items-center justify-center bg-level-0 p-margin-mobile md:p-margin-desktop">
        <div className="max-w-md text-center">
          <ErrorBanner message="No request yet. Start from Find a table." />
          <Link href="/" className="mt-md inline-block">
            <Button>Find a table</Button>
          </Link>
        </div>
      </main>
    );
  }

  const hero = data?.recommendations[0];
  const rest = data?.recommendations.slice(1) ?? [];
  const fallback = data?.meta.source === "fallback" || data?.meta.source === "rules";

  return (
    <>
      <RequestSummary request={request} />
      <main className="flex-1 overflow-y-auto bg-level-0 p-margin-mobile pb-24 md:p-margin-desktop md:pb-margin-desktop">
        <div className="mx-auto max-w-4xl space-y-lg">
          <div className="flex items-center justify-between md:hidden">
            <p className="font-geist text-label-sm uppercase tracking-wider text-on-surface-variant">
              {request.location} · {request.budget}
            </p>
            <Link href={`/?${searchParams.toString()}`}>
              <Button variant="secondary" className="py-1">
                Edit
              </Button>
            </Link>
          </div>

          {loading ? <SkeletonResults /> : null}

          {!loading && error ? <ErrorBanner message={error} onRetry={() => void load(request)} /> : null}

          {!loading && data && data.recommendations.length === 0 ? (
            <EmptyResults suggestions={data.meta.suggestions} request={request} />
          ) : null}

          {!loading && data && hero ? (
            <>
              {data.summary ? (
                <SummaryBanner summary={data.summary} fallback={fallback} />
              ) : fallback ? (
                <SummaryBanner
                  summary="A rule-based shortlist while the AI ranker is unavailable."
                  fallback
                />
              ) : null}
              <div className="space-y-lg">
                <RestaurantHeroCard item={hero} />
                {rest.map((item) => (
                  <RestaurantRowCard key={item.id} item={item} />
                ))}
              </div>
              <ResultsFooter shown={data.recommendations.length} meta={data.meta} />
            </>
          ) : null}
        </div>
      </main>
    </>
  );
}
