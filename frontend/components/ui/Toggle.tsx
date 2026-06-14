"use client";

import { cn } from "@/lib/utils";

interface ToggleProps {
  checked: boolean;
  onChange: (checked: boolean) => void;
  label?: string;
  disabled?: boolean;
  size?: "sm" | "md";
}

export function Toggle({ checked, onChange, label, disabled, size = "md" }: ToggleProps) {
  return (
    <label className={cn(
      "inline-flex items-center gap-3 cursor-pointer",
      disabled && "opacity-50 cursor-not-allowed"
    )}>
      <div className="relative">
        <input
          type="checkbox"
          checked={checked}
          onChange={(e) => !disabled && onChange(e.target.checked)}
          className="sr-only"
        />
        <div
          className={cn(
            "rounded-full transition-colors duration-200",
            size === "md" && "w-11 h-6",
            size === "sm" && "w-8 h-4.5",
            checked
              ? "bg-[rgb(var(--color-accent))]"
              : "bg-[rgb(var(--color-border))]"
          )}
        />
        <div
          className={cn(
            "absolute top-0.5 left-0.5 bg-white rounded-full shadow-sm transition-transform duration-200",
            size === "md" && "w-5 h-5",
            size === "sm" && "w-3.5 h-3.5",
            checked && (size === "md" ? "translate-x-5" : "translate-x-3.5")
          )}
        />
      </div>
      {label && (
        <span className="font-display text-sm font-semibold text-[rgb(var(--color-text))]">{label}</span>
      )}
    </label>
  );
}
