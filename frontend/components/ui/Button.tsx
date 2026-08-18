import type { ButtonHTMLAttributes } from "react";
import { cn } from "@/lib/cn";

type Variant = "primary" | "secondary" | "ghost";

interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: Variant;
}

const variants: Record<Variant, string> = {
  primary:
    "bg-primary-container text-on-primary-container hover:bg-primary disabled:opacity-50",
  secondary:
    "bg-transparent hairline text-on-surface hover:bg-surface-container disabled:opacity-50",
  ghost:
    "bg-transparent text-on-surface-variant hover:bg-surface-container hover:text-on-surface disabled:opacity-50",
};

export function Button({ variant = "primary", className, type = "button", ...props }: ButtonProps) {
  return (
    <button
      type={type}
      className={cn(
        "inline-flex items-center justify-center gap-2 rounded-lg px-md py-sm font-geist text-label-md transition-colors duration-200",
        variants[variant],
        className,
      )}
      {...props}
    />
  );
}
