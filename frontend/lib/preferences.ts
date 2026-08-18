import type { BudgetBand, PreferenceFormState, RecommendRequest } from "./types";

export const DEMO_PRESET: PreferenceFormState = {
  location: "Indiranagar",
  budget: "medium",
  cuisine: ["Italian"],
  min_rating: 4,
  additional_preferences: "romantic rooftop",
  top_k: 5,
};

export const EMPTY_FORM: PreferenceFormState = {
  location: "",
  budget: "medium",
  cuisine: [],
  min_rating: 3.5,
  additional_preferences: "",
  top_k: 5,
};

export const FALLBACK_CUISINES = [
  "South Indian",
  "North Indian",
  "Italian",
  "Chinese",
  "Continental",
];

export const VIBE_CHIPS = ["family-friendly", "romantic", "rooftop"] as const;

const FEATURED_CUISINES = [
  "South Indian",
  "North Indian",
  "Italian",
  "Chinese",
  "Continental",
  "Cafe",
  "Biryani",
  "Fast Food",
];

export function featuredCuisines(catalog: string[]): string[] {
  if (!catalog.length) {
    return FALLBACK_CUISINES;
  }
  const lower = new Map(catalog.map((item) => [item.toLowerCase(), item]));
  const picked: string[] = [];
  for (const name of FEATURED_CUISINES) {
    const match = lower.get(name.toLowerCase());
    if (match) {
      picked.push(match);
    }
  }
  for (const item of catalog) {
    if (picked.length >= 10) {
      break;
    }
    if (!picked.some((p) => p.toLowerCase() === item.toLowerCase())) {
      picked.push(item);
    }
  }
  return picked;
}

function isBudget(value: string): value is BudgetBand {
  return value === "low" || value === "medium" || value === "high";
}

export function parsePreferences(params: URLSearchParams): PreferenceFormState | null {
  const location = params.get("location")?.trim() ?? "";
  if (!location) {
    return null;
  }
  const budgetRaw = (params.get("budget") ?? "medium").toLowerCase();
  const cuisine = params
    .getAll("cuisine")
    .flatMap((value) => value.split(","))
    .map((item) => item.trim())
    .filter(Boolean);
  const minRating = Number(params.get("min_rating") ?? "3.5");
  const topK = Number(params.get("top_k") ?? "5");
  return {
    location,
    budget: isBudget(budgetRaw) ? budgetRaw : "medium",
    cuisine,
    min_rating: Number.isFinite(minRating) ? Math.min(5, Math.max(0, minRating)) : 3.5,
    additional_preferences: params.get("additional_preferences") ?? "",
    top_k: Number.isFinite(topK) ? Math.min(10, Math.max(1, Math.round(topK))) : 5,
  };
}

export function toSearchParams(state: PreferenceFormState): string {
  const params = new URLSearchParams();
  params.set("location", state.location.trim());
  params.set("budget", state.budget);
  state.cuisine.forEach((item) => params.append("cuisine", item));
  params.set("min_rating", String(state.min_rating));
  params.set("top_k", String(state.top_k));
  if (state.additional_preferences.trim()) {
    params.set("additional_preferences", state.additional_preferences.trim());
  }
  return params.toString();
}

export function toRecommendRequest(state: PreferenceFormState): RecommendRequest {
  return {
    location: state.location.trim(),
    budget: state.budget,
    cuisine: state.cuisine,
    min_rating: state.min_rating,
    additional_preferences: state.additional_preferences.trim(),
    top_k: state.top_k,
  };
}

export function appendVibe(current: string, chip: string): string {
  const existing = current.toLowerCase();
  if (existing.includes(chip.toLowerCase())) {
    return current;
  }
  return current.trim() ? `${current.trim()} ${chip}` : chip;
}

export function resultsHref(state: PreferenceFormState): string {
  return `/results?${toSearchParams(state)}`;
}

export function editHref(state: PreferenceFormState): string {
  return `/?${toSearchParams(state)}`;
}
