import Link from "next/link";
import type { ReactNode } from "react";
import { BrandMark } from "@/components/app-shell/BrandMark";
import { Icon } from "@/components/ui/Icon";
import { cn } from "@/lib/cn";

const NAV = [
  { href: "/", label: "Recommendations", short: "Recs", icon: "auto_awesome", live: true },
  { href: "#", label: "Saved", short: "Saved", icon: "bookmark", live: false },
  { href: "#", label: "History", short: "History", icon: "history", live: false },
  { href: "#", label: "Settings", short: "Settings", icon: "settings", live: false },
] as const;

export function AppShell({ children }: { children: ReactNode }) {
  return (
    <div className="flex min-h-screen flex-col bg-level-0 antialiased md:flex-row">
      <header className="fixed top-0 z-50 flex h-16 w-full items-center justify-between border-b border-outline-variant bg-surface px-margin-mobile md:hidden">
        <BrandMark size="sm" />
        <div className="flex items-center gap-4 text-primary">
          <Icon name="location_on" className="rounded p-1" />
          <Icon name="tune" className="rounded p-1" />
        </div>
      </header>

      <nav className="fixed left-0 top-0 z-40 hidden h-screen w-64 flex-col border-r border-outline-variant bg-surface-container p-md md:flex">
        <div className="mb-lg">
          <h1 className="mb-1">
            <Link href="/" className="inline-block">
              <BrandMark />
            </Link>
          </h1>
          <div className="inline-block rounded border border-outline-variant bg-surface-container-high px-2 py-1 font-geist text-label-sm text-on-surface-variant">
            Bangalore catalog
          </div>
        </div>
        <ul className="flex flex-grow flex-col space-y-2">
          {NAV.map((item) =>
            item.live ? (
              <li key={item.label}>
                <Link
                  href={item.href}
                  className="group flex items-center gap-3 rounded-md border-r-2 border-primary px-3 py-2 font-bold text-primary transition-all duration-200 hover:bg-surface-container-high"
                >
                  <Icon name={item.icon} />
                  <span className="font-geist text-body-md">{item.label}</span>
                </Link>
              </li>
            ) : (
              <li key={item.label}>
                <span
                  title="Coming soon"
                  className="flex cursor-not-allowed items-center gap-3 rounded-md px-3 py-2 text-on-surface-variant opacity-50"
                >
                  <Icon name={item.icon} />
                  <span className="font-geist text-body-md">{item.label}</span>
                </span>
              </li>
            ),
          )}
        </ul>
        <div className="mt-auto flex items-center gap-3 border-t border-outline-variant pt-4 opacity-50" title="Coming soon">
          <div className="flex h-8 w-8 items-center justify-center overflow-hidden rounded-full border border-outline bg-surface-container-highest">
            <Icon name="person" className="text-sm text-on-surface-variant" />
          </div>
          <div className="font-geist text-label-md text-on-surface">Account</div>
        </div>
      </nav>

      <div
        className={cn(
          "relative flex w-full flex-1 flex-col overflow-hidden md:ml-64 md:h-screen md:flex-row",
          "mt-16 h-[calc(100vh-4rem)] pb-16 md:mt-0 md:pb-0",
        )}
      >
        {children}
      </div>

      <nav className="fixed bottom-0 left-0 z-50 flex w-full flex-row items-center justify-between border-t border-outline-variant bg-surface-container-lowest px-margin-mobile py-sm md:hidden">
        {NAV.map((item) =>
          item.live ? (
            <Link
              key={item.label}
              href={item.href}
              className="flex flex-1 flex-col items-center gap-1 text-primary"
            >
              <Icon name={item.icon} />
              <span className="font-geist text-label-sm">{item.short}</span>
            </Link>
          ) : (
            <span
              key={item.label}
              title="Coming soon"
              className="flex flex-1 cursor-not-allowed flex-col items-center gap-1 text-on-surface-variant opacity-50"
            >
              <Icon name={item.icon} />
              <span className="font-geist text-label-sm">{item.short}</span>
            </span>
          ),
        )}
      </nav>
    </div>
  );
}
