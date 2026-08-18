import { formatCost, formatRating, splitCuisines, truncate } from "@/lib/format";
import type { RecommendationItem } from "@/lib/types";

export function RestaurantRowCard({ item }: { item: RecommendationItem }) {
  const cuisines = splitCuisines(item.cuisine);
  return (
    <article className="flex flex-col items-start gap-md rounded-lg bg-level-2 p-md hairline transition-colors duration-200 hover:bg-[#222B33] sm:flex-row">
      <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-full bg-surface font-newsreader text-headline-md-mobile text-on-surface-variant hairline">
        {item.rank}
      </div>
      <div className="min-w-0 flex-1 space-y-sm">
        <h3 className="break-words font-newsreader text-headline-md-mobile text-on-surface sm:text-headline-md">
          {truncate(item.name, 80)}
        </h3>
        <div className="flex flex-wrap items-center gap-sm font-geist text-label-md text-on-surface-variant">
          <span>{item.location || "N/A"}</span>
          {cuisines[0] ? (
            <>
              <span>•</span>
              <span className="uppercase tracking-wider">{cuisines[0]}</span>
            </>
          ) : null}
          <span>•</span>
          <span>{formatCost(item.estimated_cost)}</span>
          <span>•</span>
          <span className={item.rating == null ? "" : "text-tomato"}>{formatRating(item.rating)}</span>
        </div>
        {item.explanation ? (
          <p className="font-newsreader italic text-gold line-clamp-2">{item.explanation}</p>
        ) : null}
      </div>
    </article>
  );
}
