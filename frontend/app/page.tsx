import { Suspense } from "react";
import { FindTableView } from "@/components/preference-form/FindTableView";

export default function HomePage() {
  return (
    <Suspense fallback={<FindFallback />}>
      <FindTableView />
    </Suspense>
  );
}

function FindFallback() {
  return (
    <>
      <aside className="h-full w-full shrink-0 bg-level-1 md:w-[380px]" />
      <section className="flex flex-1 items-center justify-center bg-level-0" />
    </>
  );
}
