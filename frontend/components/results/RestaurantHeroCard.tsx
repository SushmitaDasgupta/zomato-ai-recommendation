import { formatCost, formatRating, splitCuisines, truncate } from "@/lib/format";
import { AiQuote } from "@/components/results/AiQuote";
import type { RecommendationItem } from "@/lib/types";

export function RestaurantHeroCard({ item }: { item: RecommendationItem }) {
  const cuisines = splitCuisines(item.cuisine);
  return (
    <article className="overflow-hidden rounded-xl bg-level-2 hairline">
      <div className="space-y-md p-md md:p-lg">
        <div className="flex items-start gap-md">
          <div className="flex h-12 w-12 shrink-0 items-center justify-center rounded-full bg-tomato font-newsreader text-headline-md text-on-tomato shadow-[0_0_15px_rgba(226,61,40,0.4)]">
            {item.rank}
          </div>
          <div className="min-w-0 flex-1">
            <h3 className="mb-xs break-words font-newsreader text-headline-md-mobile text-on-surface md:text-display-lg">
              {truncate(item.name, 80)}
            </h3>
            <div className="flex flex-wrap items-center gap-sm font-geist text-label-md text-on-surface-variant">
              <span>{item.location || "N/A"}</span>
              <span>•</span>
              <span>{formatCost(item.estimated_cost)}</span>
              <span>•</span>
              <RatingRow rating={item.rating} />
            </div>
          </div>
        </div>
        {cuisines.length ? (
          <div className="flex flex-wrap gap-sm">
            {cuisines.map((label) => (
              <span
                key={label}
                className="rounded bg-surface px-sm py-xs font-geist text-label-sm uppercase tracking-wider text-on-surface-variant hairline"
              >
                {label}
              </span>
            ))}
          </div>
        ) : null}
        <AiQuote text={item.explanation} />
      </div>
    </article>
  );
}

function RatingRow({ rating }: { rating: number | null }) {
  const label = formatRating(rating);
  if (label === "N/A") {
    return <span>N/A</span>;
  }
  const filled = Math.round(rating ?? 0);
  return (
    <div className="flex items-center gap-xs">
      <span className="text-tomato">{label}</span>
      <div className="flex gap-[2px]" aria-hidden>
        {Array.from({ length: 5 }, (_, index) => (
          <span
            key={index}
            className={`h-2 w-2 rounded-full bg-tomato ${index < filled ? "" : "opacity-50"}`}
          />
        ))}
      </div>
    </div>
  );
}
