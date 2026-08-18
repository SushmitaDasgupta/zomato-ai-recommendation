export function SkeletonResults() {
  return (
    <div className="space-y-lg" aria-busy="true" aria-live="polite">
      <div className="h-20 rounded-lg bg-level-1 hairline" />
      <div className="space-y-md rounded-xl bg-level-2 p-lg hairline">
        <div className="flex gap-md">
          <div className="h-12 w-12 rounded-full bg-surface" />
          <div className="flex-1 space-y-sm">
            <div className="h-10 w-2/3 rounded bg-surface" />
            <div className="h-4 w-1/2 rounded bg-surface" />
          </div>
        </div>
        <div className="h-16 rounded bg-surface" />
      </div>
      {Array.from({ length: 4 }, (_, index) => (
        <div key={index} className="flex gap-md rounded-lg bg-level-2 p-md hairline">
          <div className="h-10 w-10 rounded-full bg-surface" />
          <div className="flex-1 space-y-sm">
            <div className="h-6 w-1/2 rounded bg-surface" />
            <div className="h-4 w-1/3 rounded bg-surface" />
          </div>
        </div>
      ))}
    </div>
  );
}
