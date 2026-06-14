"use client";

import { cn } from "@/lib/utils";

interface Tab {
  id: string;
  label: string;
  count?: number;
}

interface TabsProps {
  tabs: Tab[];
  active: string;
  onChange: (id: string) => void;
  variant?: "underline" | "pills" | "cards";
  className?: string;
}

export function Tabs({ tabs, active, onChange, variant = "underline", className }: TabsProps) {
  return (
    <div className={cn("flex gap-1", className)}>
      {tabs.map((tab) => (
        <button
          key={tab.id}
          onClick={() => onChange(tab.id)}
          className={cn(
            "font-display font-semibold text-sm transition-all duration-150 whitespace-nowrap",
            variant === "underline" &&
              (active === tab.id
                ? "py-2 px-3 text-[rgb(var(--color-text))] border-b-2 border-[rgb(var(--color-accent))]"
                : "py-2 px-3 text-[rgb(var(--color-text-secondary))] hover:text-[rgb(var(--color-text))] border-b-2 border-transparent"),
            variant === "pills" &&
              (active === tab.id
                ? "py-1.5 px-3 bg-[rgb(var(--color-accent))] text-white rounded-lg"
                : "py-1.5 px-3 text-[rgb(var(--color-text-secondary))] hover:text-[rgb(var(--color-text))] hover:bg-[rgb(var(--color-accent-soft))]/50 rounded-lg"),
            variant === "cards" &&
              (active === tab.id
                ? "py-2 px-4 bg-[rgb(var(--color-surface))] border border-[rgb(var(--color-border))] rounded-t-lg border-b-0 -mb-px text-[rgb(var(--color-text))]"
                : "py-2 px-4 text-[rgb(var(--color-text-secondary))] hover:text-[rgb(var(--color-text))]")
          )}
        >
          <span className="inline-flex items-center gap-1.5">
            {tab.label}
            {tab.count !== undefined && (
              <span className={cn(
                "text-xs px-1.5 py-0.5 rounded-full",
                active === tab.id && variant === "pills"
                  ? "bg-white/20"
                  : "bg-[rgb(var(--color-accent-soft))]"
              )}>
                {tab.count}
              </span>
            )}
          </span>
        </button>
      ))}
    </div>
  );
}
