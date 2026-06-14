"use client";

import { cn } from "@/lib/utils";

interface KpiCardProps {
  icon: string;
  value: string;
  label: string;
  trend?: { value: string; positive: boolean };
  color?: "navy" | "terra" | "emerald" | "amber";
  isLoading?: boolean;
  className?: string;
}

const colorConfig: Record<string, { from: string; to: string }> = {
  navy: { from: "#3a5f84", to: "#1f3a55" },
  terra: { from: "#b6612e", to: "#733b1b" },
  emerald: { from: "#059669", to: "#065f46" },
  amber: { from: "#f59e0b", to: "#b45309" },
};

export function KpiCard({ icon, value, label, trend, color = "navy", isLoading, className }: KpiCardProps) {
  const c = colorConfig[color];
  return (
    <div
      className={cn(
        "relative overflow-hidden rounded-xl p-5 text-white shadow-[0_4px_20px_rgba(0,0,0,0.15)] transition-all duration-200 hover:shadow-[0_8px_30px_rgba(0,0,0,0.2)] hover:-translate-y-0.5",
        className
      )}
      style={{ backgroundImage: `linear-gradient(to bottom right, ${c.from}, ${c.to})` }}
    >
      <div className="absolute top-3 left-3 text-3xl opacity-15 select-none">{icon}</div>
      <div className="relative z-10">
        <p className="font-display text-3xl font-extrabold mb-1">
          {isLoading ? (
            <span className="inline-block w-20 h-9 bg-white/20 rounded animate-pulse" />
          ) : (
            value
          )}
        </p>
        <p className="text-sm font-display font-semibold opacity-85">{label}</p>
        {trend && (
          <div className="flex items-center gap-1 mt-2 text-xs font-semibold opacity-80">
            <span>{trend.positive ? "↑" : "↓"}</span>
            <span>{trend.value}</span>
          </div>
        )}
      </div>
    </div>
  );
}
