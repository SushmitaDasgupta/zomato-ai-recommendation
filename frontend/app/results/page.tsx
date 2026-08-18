import { Suspense } from "react";
import { ResultsView } from "@/components/results/ResultsView";
import { SkeletonResults } from "@/components/results/SkeletonResults";

export default function ResultsPage() {
  return (
    <Suspense
      fallback={
        <main className="flex-1 bg-level-0 p-margin-desktop">
          <div className="mx-auto max-w-4xl">
            <SkeletonResults />
          </div>
        </main>
      }
    >
      <ResultsView />
    </Suspense>
  );
}
