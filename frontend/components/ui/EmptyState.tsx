import { cn } from "@/lib/utils";
import { Button } from "./button";

interface EmptyStateProps {
  icon?: string;
  title: string;
  description?: string;
  actionLabel?: string;
  onAction?: () => void;
  className?: string;
}

export function EmptyState({ icon = "📭", title, description, actionLabel, onAction, className }: EmptyStateProps) {
  return (
    <div className={cn("flex flex-col items-center justify-center py-16 text-center", className)}>
      <span className="text-5xl mb-4 block">{icon}</span>
      <h3 className="font-display text-lg font-bold mb-1">{title}</h3>
      {description && (
        <p className="text-sm text-[rgb(var(--color-text-secondary))] mb-4 max-w-xs">
          {description}
        </p>
      )}
      {actionLabel && onAction && (
        <Button onClick={onAction}>{actionLabel}</Button>
      )}
    </div>
  );
}
