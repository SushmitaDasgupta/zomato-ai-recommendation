"use client";

import { DEMO_PRESET } from "@/lib/preferences";
import { Icon } from "@/components/ui/Icon";

export function EmptyCanvas({ onApplyPreset }: { onApplyPreset: () => void }) {
  return (
    <section className="relative flex min-h-[240px] flex-1 flex-col overflow-hidden bg-level-0">
      <div className="relative z-10 flex flex-1 flex-col items-center justify-center p-md text-center md:p-margin-desktop">
        <div className="mx-auto w-full max-w-md space-y-6">
          <button
            type="button"
            onClick={onApplyPreset}
            className="flex cursor-pointer flex-wrap items-center justify-center gap-2 opacity-60 transition-opacity hover:opacity-100"
          >
            <Icon name="magic_button" className="text-sm text-secondary" />
            <div className="flex items-center gap-1.5 rounded-full border border-outline-variant bg-level-1 px-3 py-1 font-geist text-label-sm uppercase tracking-wider text-on-surface-variant">
              {DEMO_PRESET.location}
              <span className="mx-1">·</span>
              {DEMO_PRESET.cuisine[0]}
              <span className="mx-1">·</span>
              {DEMO_PRESET.budget}
              <span className="mx-1">·</span>
              Romantic rooftop
            </div>
          </button>
          <h2 className="font-newsreader text-title-lg text-on-surface">
            We&apos;ll filter the catalog first,
            <br />
            then rank a shortlist.
          </h2>
          <p className="font-geist text-body-md text-on-surface-variant">
            Adjust parameters on the left to begin generating.
          </p>
        </div>
      </div>
    </section>
  );
}
