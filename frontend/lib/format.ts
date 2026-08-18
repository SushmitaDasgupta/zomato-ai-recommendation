export function formatCost(value: number | null | undefined): string {
  if (value == null || Number.isNaN(value)) {
    return "N/A";
  }
  return `₹${Math.round(value).toLocaleString("en-IN")} for two`;
}

export function formatRating(value: number | null | undefined): string {
  if (value == null || Number.isNaN(value)) {
    return "N/A";
  }
  return value.toFixed(1);
}

export function formatLatency(ms: number | null | undefined): string {
  if (ms == null || Number.isNaN(ms)) {
    return "—";
  }
  if (ms < 1000) {
    return `${ms}ms`;
  }
  return `${(ms / 1000).toFixed(1)}s`;
}

export function splitCuisines(value: string | null | undefined): string[] {
  if (!value || value === "N/A") {
    return [];
  }
  return value
    .split(",")
    .map((item) => item.trim())
    .filter(Boolean);
}

export function truncate(value: string, max = 72): string {
  const cleaned = value.trim();
  if (cleaned.length <= max) {
    return cleaned;
  }
  return `${cleaned.slice(0, max - 1).trimEnd()}…`;
}

export function titleBudget(budget: string): string {
  if (!budget) {
    return "—";
  }
  return budget.charAt(0).toUpperCase() + budget.slice(1);
}
