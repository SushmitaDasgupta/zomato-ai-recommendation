import { formatLatency } from "@/lib/format";
import type { RecommendMeta } from "@/lib/types";

export function ResultsFooter({ shown, meta }: { shown: number; meta: RecommendMeta }) {
  return (
    <footer className="mt-lg flex w-full max-w-4xl flex-col items-center justify-between pt-md hairline-t md:flex-row">
      <p className="font-geist text-label-sm text-on-surface-variant">
        {shown} shown • {meta.candidates_considered} candidates • {formatLatency(meta.latency_ms)}
      </p>
    </footer>
  );
}
