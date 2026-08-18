import type { ButtonHTMLAttributes } from "react";
import { cn } from "@/lib/cn";

interface ChipProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  selected?: boolean;
  tone?: "default" | "gold";
}

export function Chip({ selected = false, tone = "default", className, type = "button", ...props }: ChipProps) {
  return (
    <button
      type={type}
      className={cn(
        "rounded border px-3 py-1 font-geist text-label-md transition-colors duration-200",
        selected
          ? "border-primary-container bg-primary-container text-on-primary-container"
          : tone === "gold"
            ? "border-outline-variant/50 bg-transparent text-secondary hover:bg-surface-container"
            : "border-outline-variant bg-transparent text-on-surface-variant hover:border-outline hover:text-on-surface",
        className,
      )}
      {...props}
    />
  );
}
