import Link from "next/link";
import { Button } from "@/components/ui/Button";
import { editHref } from "@/lib/preferences";
import type { PreferenceFormState } from "@/lib/types";

export function EmptyResults({
  suggestions,
  request,
}: {
  suggestions: string[];
  request: PreferenceFormState;
}) {
  return (
    <div className="rounded-lg bg-level-1 p-lg text-center hairline">
      <h2 className="mb-sm font-newsreader text-title-lg text-on-surface">No tables matched those filters</h2>
      <p className="mb-md font-geist text-body-md text-on-surface-variant">
        Relax location, cuisine, rating, or budget and try again.
      </p>
      {suggestions.length ? (
        <ul className="mx-auto mb-lg max-w-lg space-y-sm text-left font-geist text-body-md text-on-surface-variant">
          {suggestions.map((tip) => (
            <li key={tip}>• {tip}</li>
          ))}
        </ul>
      ) : null}
      <Link href={editHref(request)}>
        <Button variant="secondary">Edit Request</Button>
      </Link>
    </div>
  );
}
