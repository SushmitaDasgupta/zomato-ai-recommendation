import type { InputHTMLAttributes, ReactNode } from "react";
import { cn } from "@/lib/cn";

interface InputProps extends InputHTMLAttributes<HTMLInputElement> {
  leading?: ReactNode;
}

export function Input({ leading, className, ...props }: InputProps) {
  return (
    <div className="relative">
      {leading ? (
        <span className="pointer-events-none absolute left-3 top-1/2 -translate-y-1/2 text-on-surface-variant">
          {leading}
        </span>
      ) : null}
      <input
        className={cn(
          "w-full rounded-md border border-outline-variant bg-level-1 py-2 pr-3 font-geist text-body-md text-on-surface placeholder:text-surface-variant focus-tomato",
          leading ? "pl-10" : "pl-3",
          className,
        )}
        {...props}
      />
    </div>
  );
}
