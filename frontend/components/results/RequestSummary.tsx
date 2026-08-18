import Link from "next/link";
import { Button } from "@/components/ui/Button";
import { Icon } from "@/components/ui/Icon";
import { titleBudget } from "@/lib/format";
import { editHref } from "@/lib/preferences";
import type { PreferenceFormState } from "@/lib/types";

export function RequestSummary({ request }: { request: PreferenceFormState }) {
  return (
    <aside className="hidden h-full w-[380px] shrink-0 flex-col overflow-y-auto bg-level-1 p-lg hairline-r md:flex">
      <h2 className="mb-lg font-newsreader text-headline-md text-on-surface">Your Request</h2>
      <div className="space-y-md">
        <Field label="Location" icon="location_on" value={request.location} />
        <Field label="Budget" icon="payments" value={titleBudget(request.budget)} />
        <div className="flex flex-col gap-xs">
          <span className="font-geist text-label-sm uppercase tracking-wider text-on-surface-variant">
            Cuisine
          </span>
          <div className="flex flex-wrap gap-sm">
            {request.cuisine.length ? (
              request.cuisine.map((item) => (
                <span
                  key={item}
                  className="rounded-full bg-surface px-md py-sm font-geist text-label-md text-on-surface hairline"
                >
                  {item}
                </span>
              ))
            ) : (
              <span className="font-geist text-body-md text-on-surface-variant">Any</span>
            )}
          </div>
        </div>
        <div className="flex flex-col gap-xs">
          <span className="font-geist text-label-sm uppercase tracking-wider text-on-surface-variant">
            Min rating
          </span>
          <div className="flex items-center gap-sm rounded-lg bg-surface p-sm hairline">
            <Icon name="star" className="text-on-surface-variant" />
            <span className="font-geist text-body-lg text-on-surface">{request.min_rating.toFixed(1)}+</span>
          </div>
        </div>
        <div className="flex flex-col gap-xs">
          <span className="font-geist text-label-sm uppercase tracking-wider text-on-surface-variant">
            Preferences
          </span>
          <textarea
            readOnly
            value={request.additional_preferences || "—"}
            className="h-32 w-full resize-none rounded-lg bg-surface p-md font-geist text-body-lg text-on-surface hairline focus-tomato"
          />
        </div>
      </div>
      <div className="mt-auto pt-lg">
        <Link href={editHref(request)} className="block">
          <Button variant="secondary" className="w-full">
            Edit Request
          </Button>
        </Link>
      </div>
    </aside>
  );
}

function Field({ label, icon, value }: { label: string; icon: string; value: string }) {
  return (
    <div className="flex flex-col gap-xs">
      <span className="font-geist text-label-sm uppercase tracking-wider text-on-surface-variant">
        {label}
      </span>
      <div className="flex items-center gap-sm rounded-lg bg-surface p-sm hairline">
        <Icon name={icon} className="text-on-surface-variant" />
        <span className="font-geist text-body-lg text-on-surface">{value}</span>
      </div>
    </div>
  );
}
