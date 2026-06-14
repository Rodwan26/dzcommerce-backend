"use client";

import { useLocale } from "next-intl";
import { useRouter } from "next/navigation";
import { setCookie } from "@/lib/utils";
import { cn } from "@/lib/utils";
import { useState, useRef, useEffect } from "react";

const languages = [
  { code: "ar", label: "العربية", flag: "🇩🇿" },
  { code: "fr", label: "Français", flag: "🇫🇷" },
  { code: "en", label: "English", flag: "🇬🇧" },
];

export default function LanguageSwitcher({ mini = false }: { mini?: boolean }) {
  const locale = useLocale();
  const router = useRouter();
  const [open, setOpen] = useState(false);
  const ref = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const handler = (e: MouseEvent) => {
      if (ref.current && !ref.current.contains(e.target as Node)) setOpen(false);
    };
    document.addEventListener("mousedown", handler);
    return () => document.removeEventListener("mousedown", handler);
  }, []);

  function switchLang(code: string) {
    setCookie("NEXT_LOCALE", code, 365);
    router.refresh();
    setOpen(false);
  }

  const current = languages.find((l) => l.code === locale) || languages[0];

  if (mini) {
    return (
      <div ref={ref} className="relative">
        <button
          onClick={() => setOpen(!open)}
          className="flex items-center gap-1.5 px-2 py-1 rounded-lg text-xs font-semibold text-[rgb(var(--color-text-secondary))] hover:text-[rgb(var(--color-text))] hover:bg-[rgb(var(--color-accent-soft))] transition-colors"
        >
          <span>{current.flag}</span>
        </button>
        {open && (
          <div className="absolute top-full mt-1 left-0 z-50 min-w-[130px] bg-[rgb(var(--color-surface))] border border-[rgb(var(--color-border))] rounded-lg shadow-lg py-1 animate-scale-in">
            {languages.map((l) => (
              <button
                key={l.code}
                onClick={() => switchLang(l.code)}
                className={cn(
                  "flex items-center gap-2 w-full px-3 py-2 text-sm font-display font-semibold transition-colors text-right",
                  locale === l.code
                    ? "text-[rgb(var(--color-accent))] bg-[rgb(var(--color-accent-soft))]"
                    : "text-[rgb(var(--color-text))] hover:bg-[rgb(var(--color-accent-soft))]/50"
                )}
              >
                <span>{l.flag}</span>
                {l.label}
              </button>
            ))}
          </div>
        )}
      </div>
    );
  }

  return (
    <div ref={ref} className="relative">
      <button
        onClick={() => setOpen(!open)}
        className="flex items-center gap-2 w-full px-3 py-2 rounded-lg text-sm font-display font-semibold text-[rgb(var(--color-text-secondary))] hover:text-[rgb(var(--color-text))] hover:bg-[rgb(var(--color-accent-soft))] transition-colors"
      >
        <span>{current.flag}</span>
        <span className="flex-1 text-right">{current.label}</span>
        <svg className={cn("w-3.5 h-3.5 transition-transform", open && "rotate-180")} fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
          <path strokeLinecap="round" strokeLinejoin="round" d="M19 9l-7 7-7-7" />
        </svg>
      </button>
      {open && (
        <div className="absolute bottom-full mb-1 left-0 right-0 z-50 bg-[rgb(var(--color-surface))] border border-[rgb(var(--color-border))] rounded-lg shadow-lg py-1 animate-scale-in">
          {languages.filter((l) => l.code !== locale).map((l) => (
            <button
              key={l.code}
              onClick={() => switchLang(l.code)}
              className="flex items-center gap-2 w-full px-3 py-2 text-sm font-display font-semibold text-[rgb(var(--color-text))] hover:bg-[rgb(var(--color-accent-soft))]/50 transition-colors text-right"
            >
              <span>{l.flag}</span>
              {l.label}
            </button>
          ))}
        </div>
      )}
    </div>
  );
}
