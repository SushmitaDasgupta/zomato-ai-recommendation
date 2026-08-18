export type BudgetBand = "low" | "medium" | "high";

export type RecommendationSource = "llm" | "fallback" | "rules" | string;

export interface RecommendRequest {
  location: string;
  budget: BudgetBand;
  cuisine: string[];
  min_rating: number;
  additional_preferences: string;
  top_k: number;
}

export interface RecommendationItem {
  rank: number;
  id: string;
  name: string;
  cuisine: string;
  rating: number | null;
  estimated_cost: number | null;
  location: string;
  explanation: string;
  match_score: number;
  source: RecommendationSource;
  fit_notes: string[];
}

export interface LatencyBreakdown {
  normalize_ms: number;
  filter_ms: number;
  llm_ms: number;
  assemble_ms: number;
  total_ms: number;
}

export interface RecommendMeta {
  candidates_considered: number;
  filters_applied: string[];
  relaxations_applied: string[];
  source: RecommendationSource;
  latency_ms: number | null;
  empty_reason: string | null;
  suggestions: string[];
  llm_model: string | null;
  fallback_reason: string | null;
  request_id: string | null;
  cache_hit: boolean;
  filter_stage_counts: Record<string, number>;
  latency_breakdown: LatencyBreakdown | null;
}

export interface RecommendResponse {
  summary: string | null;
  recommendations: RecommendationItem[];
  meta: RecommendMeta;
}

export interface BudgetBounds {
  low_max: number;
  medium_max: number;
  unit: string;
}

export interface FilterMetaResponse {
  cities: string[];
  locations: string[];
  cuisines: string[];
  budget_bands: BudgetBand[];
  budget_bounds: BudgetBounds;
  min_rating_default: number;
  rating_range: number[];
  top_k_default: number;
  top_k_range: number[];
  additional_preference_hints: string[];
  default_location: string | null;
  catalog_rows: number;
}

export interface PreferenceFormState {
  location: string;
  budget: BudgetBand;
  cuisine: string[];
  min_rating: number;
  additional_preferences: string;
  top_k: number;
}
