import { Button } from "@/components/ui/Button";

export function ErrorBanner({ message, onRetry }: { message: string; onRetry?: () => void }) {
  return (
    <div className="flex flex-col items-start gap-md rounded-lg border border-error-container bg-level-1 p-md md:flex-row md:items-center">
      <p className="flex-1 font-geist text-body-md text-error">{message}</p>
      {onRetry ? (
        <Button variant="secondary" onClick={onRetry}>
          Retry
        </Button>
      ) : null}
    </div>
  );
}
