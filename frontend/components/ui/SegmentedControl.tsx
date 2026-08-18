import { cn } from "@/lib/cn";

interface Option<T extends string> {
  value: T;
  label: string;
}

interface SegmentedControlProps<T extends string> {
  name: string;
  value: T;
  options: Option<T>[];
  onChange: (value: T) => void;
  "aria-labelledby"?: string;
}

export function SegmentedControl<T extends string>({
  name,
  value,
  options,
  onChange,
  "aria-labelledby": ariaLabelledBy,
}: SegmentedControlProps<T>) {
  return (
    <div
      role="radiogroup"
      aria-labelledby={ariaLabelledBy}
      className="flex overflow-hidden rounded-md border border-outline-variant bg-level-0 p-[2px]"
    >
      {options.map((option) => {
        const selected = option.value === value;
        return (
          <button
            key={option.value}
            type="button"
            role="radio"
            aria-checked={selected}
            name={name}
            onClick={() => onChange(option.value)}
            className={cn(
              "flex-1 rounded-sm py-1.5 text-center font-geist text-label-md transition-colors duration-200",
              selected
                ? "border border-primary-container bg-primary-container text-on-primary-container"
                : "text-on-surface-variant hover:text-on-surface",
            )}
          >
            {option.label}
          </button>
        );
      })}
    </div>
  );
}
