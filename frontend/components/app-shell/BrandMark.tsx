import { cn } from "@/lib/cn";

export function BrandMark({ className, size = "md" }: { className?: string; size?: "sm" | "md" }) {
  return (
    <span
      className={cn(
        "font-newsreader italic text-primary",
        size === "sm" ? "text-headline-md-mobile" : "text-headline-md",
        className,
      )}
    >
      Tablepick
    </span>
  );
}
