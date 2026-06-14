import { cn } from "@/lib/utils";

interface SkeletonProps {
  className?: string;
  variant?: "text" | "circular" | "rectangular";
  count?: number;
}

export function Skeleton({ className, variant = "text", count = 1 }: SkeletonProps) {
  const base = "animate-pulse bg-[rgb(var(--color-border))] rounded-md";
  const variants = {
    text: "h-4 w-full",
    circular: "h-10 w-10 rounded-full",
    rectangular: "h-24 w-full rounded-lg",
  };

  return (
    <>
      {Array.from({ length: count }).map((_, i) => (
        <div key={i} className={cn(base, variants[variant], className)} />
      ))}
    </>
  );
}

export function TableSkeleton({ rows = 5, cols = 4 }: { rows?: number; cols?: number }) {
  return (
    <div className="space-y-3 p-4">
      {Array.from({ length: rows }).map((_, r) => (
        <div key={r} className="flex gap-4">
          {Array.from({ length: cols }).map((_, c) => (
            <Skeleton key={c} className="h-5 flex-1" />
          ))}
        </div>
      ))}
    </div>
  );
}

export function CardSkeleton({ count = 1 }: { count?: number }) {
  return (
    <>
      {Array.from({ length: count }).map((_, i) => (
        <div key={i} className="card space-y-4">
          <Skeleton className="h-5 w-1/3" />
          <Skeleton className="h-9 w-2/3" />
          <Skeleton className="h-3 w-1/2" />
        </div>
      ))}
    </>
  );
}

export function PageSkeleton() {
  return (
    <div className="space-y-6 animate-fade-in">
      <div className="flex items-center justify-between">
        <div className="space-y-2">
          <Skeleton className="h-8 w-48" />
          <Skeleton className="h-4 w-72" />
        </div>
        <Skeleton className="h-10 w-28 rounded-lg" />
      </div>
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {Array.from({ length: 4 }).map((_, i) => (
          <div key={i} className="h-28 rounded-xl bg-[rgb(var(--color-border))] animate-pulse" />
        ))}
      </div>
      <div className="rounded-xl border border-[rgb(var(--color-border))] p-6 space-y-4">
        <Skeleton className="h-6 w-40" />
        {Array.from({ length: 5 }).map((_, i) => (
          <div key={i} className="flex gap-4">
            {Array.from({ length: 4 }).map((_, j) => (
              <Skeleton key={j} className="h-5 flex-1" />
            ))}
          </div>
        ))}
      </div>
    </div>
  );
}
