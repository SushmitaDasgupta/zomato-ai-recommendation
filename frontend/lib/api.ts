import type { FilterMetaResponse, RecommendRequest, RecommendResponse } from "./types";
import fallbackFilters from "./catalog-filters.json";

export class ApiError extends Error {
  status: number;
  detail: unknown;

  constructor(status: number, message: string, detail?: unknown) {
    super(message);
    this.name = "ApiError";
    this.status = status;
    this.detail = detail;
  }
}

function messageFromDetail(detail: unknown): string {
  if (typeof detail === "string") {
    return detail;
  }
  if (Array.isArray(detail) && detail.length > 0) {
    const first = detail[0] as { msg?: string; loc?: unknown };
    if (first?.msg) {
      return first.msg;
    }
  }
  if (detail && typeof detail === "object" && "message" in detail) {
    return String((detail as { message: unknown }).message);
  }
  return "Something went wrong. Try again.";
}

async function parseJson<T>(res: Response): Promise<T> {
  const data: unknown = await res.json().catch(() => ({}));
  if (!res.ok) {
    const detail =
      data && typeof data === "object" && "detail" in data
        ? (data as { detail: unknown }).detail
        : data;
    throw new ApiError(res.status, messageFromDetail(detail), detail);
  }
  return data as T;
}

function isFilterMeta(data: unknown): data is FilterMetaResponse {
  if (!data || typeof data !== "object") {
    return false;
  }
  const locations = (data as { locations?: unknown }).locations;
  return Array.isArray(locations) && locations.length > 0;
}

export async function getFilters(): Promise<FilterMetaResponse> {
  try {
    const res = await fetch("/api/meta/filters", { cache: "no-store" });
    const data: unknown = await res.json().catch(() => null);
    if (res.ok && isFilterMeta(data)) {
      return data;
    }
  } catch {
    // Use the baked catalog facets so Neighborhood still works if Railway is unset.
  }
  return fallbackFilters as FilterMetaResponse;
}

export async function recommend(body: RecommendRequest): Promise<RecommendResponse> {
  const res = await fetch("/api/recommend", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
    cache: "no-store",
  });
  return parseJson<RecommendResponse>(res);
}
