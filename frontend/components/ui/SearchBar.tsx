"use client";

import { cn } from "@/lib/utils";
import { useState, useCallback } from "react";

interface SearchBarProps {
  value: string;
  onChange: (value: string) => void;
  placeholder?: string;
  className?: string;
}

export function SearchBar({ value, onChange, placeholder = "Search...", className }: SearchBarProps) {
  const [focused, setFocused] = useState(false);

  const handleClear = useCallback(() => {
    onChange("");
  }, [onChange]);

  return (
    <div
      className={cn(
        "relative flex items-center transition-all duration-150",
        focused && "ring-2 ring-[rgb(var(--color-accent))]/20",
        className
      )}
    >
      <svg
        className="absolute right-3 w-4 h-4 text-[rgb(var(--color-text-secondary))] pointer-events-none"
        fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}
      >
        <path strokeLinecap="round" strokeLinejoin="round" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
      </svg>
      <input
        type="text"
        value={value}
        onChange={(e) => onChange(e.target.value)}
        onFocus={() => setFocused(true)}
        onBlur={() => setFocused(false)}
        placeholder={placeholder}
        className={cn(
          "w-full pr-10 pl-8 py-2 bg-[rgb(var(--color-surface))] border border-[rgb(var(--color-border))] rounded-lg font-body text-sm text-[rgb(var(--color-text))] placeholder:text-[rgb(var(--color-text-secondary))]/50 transition-all duration-150",
          "focus:outline-none focus:border-[rgb(var(--color-accent))]"
        )}
      />
      {value && (
        <button
          onClick={handleClear}
          className="absolute left-2 p-0.5 rounded-full text-[rgb(var(--color-text-secondary))] hover:text-[rgb(var(--color-text))] transition-colors"
        >
          <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
            <path strokeLinecap="round" strokeLinejoin="round" d="M6 18L18 6M6 6l12 12" />
          </svg>
        </button>
      )}
    </div>
  );
}
