import { Icon } from "@/components/ui/Icon";

export function SummaryBanner({ summary, fallback }: { summary: string; fallback?: boolean }) {
  return (
    <div className="flex items-start gap-md rounded-lg bg-level-1 p-md hairline">
      <Icon name="auto_awesome" className="mt-1 text-gold" />
      <div className="space-y-1">
        <p className="font-geist text-body-lg text-on-surface">{summary}</p>
        {fallback ? (
          <p className="font-geist text-label-sm uppercase tracking-wider text-on-surface-variant">
            Ranked without live AI — rule-based shortlist
          </p>
        ) : null}
      </div>
    </div>
  );
}
