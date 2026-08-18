import { cn } from "@/lib/cn";

interface SliderProps {
  id?: string;
  min?: number;
  max?: number;
  step?: number;
  value: number;
  onChange: (value: number) => void;
  "aria-label"?: string;
  "aria-labelledby"?: string;
}

export function Slider({
  id,
  min = 1,
  max = 5,
  step = 0.1,
  value,
  onChange,
  "aria-label": ariaLabel,
  "aria-labelledby": ariaLabelledBy,
}: SliderProps) {
  return (
    <input
      id={id}
      type="range"
      min={min}
      max={max}
      step={step}
      value={value}
      aria-valuemin={min}
      aria-valuemax={max}
      aria-valuenow={value}
      aria-label={ariaLabel}
      aria-labelledby={ariaLabelledBy}
      onChange={(event) => onChange(Number(event.target.value))}
      className={cn(
        "h-1 w-full cursor-pointer appearance-none rounded-lg bg-surface-variant accent-primary-container",
      )}
    />
  );
}
