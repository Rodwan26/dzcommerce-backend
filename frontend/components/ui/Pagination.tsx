"use client";

import { cn } from "@/lib/utils";

interface PaginationProps {
  current: number;
  total: number;
  onPage: (page: number) => void;
}

export function Pagination({ current, total, onPage }: PaginationProps) {
  if (total <= 1) return null;

  const pages: (number | "...")[] = [];
  for (let i = 1; i <= total; i++) {
    if (i === 1 || i === total || (i >= current - 1 && i <= current + 1)) {
      pages.push(i);
    } else if (pages[pages.length - 1] !== "...") {
      pages.push("...");
    }
  }

  return (
    <div className="flex items-center justify-center gap-1 mt-4">
      <button
        onClick={() => onPage(Math.max(1, current - 1))}
        disabled={current === 1}
        className="px-3 py-1.5 rounded-lg text-sm font-display font-semibold text-[rgb(var(--color-text-secondary))] hover:bg-[rgb(var(--color-accent-soft))] disabled:opacity-30 disabled:cursor-not-allowed transition-colors"
      >
        Prev
      </button>
      {pages.map((p, i) =>
        p === "..." ? (
          <span key={`e${i}`} className="px-2 text-[rgb(var(--color-text-secondary))]">...</span>
        ) : (
          <button
            key={p}
            onClick={() => onPage(p)}
            className={cn(
              "px-3 py-1.5 rounded-lg text-sm font-display font-semibold transition-colors",
              p === current
                ? "bg-[rgb(var(--color-accent))] text-white"
                : "text-[rgb(var(--color-text-secondary))] hover:bg-[rgb(var(--color-accent-soft))]"
            )}
          >
            {p}
          </button>
        )
      )}
      <button
        onClick={() => onPage(Math.min(total, current + 1))}
        disabled={current === total}
        className="px-3 py-1.5 rounded-lg text-sm font-display font-semibold text-[rgb(var(--color-text-secondary))] hover:bg-[rgb(var(--color-accent-soft))] disabled:opacity-30 disabled:cursor-not-allowed transition-colors"
      >
        Next
      </button>
    </div>
  );
}
