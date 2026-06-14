"use client";
export const dynamic = "force-dynamic";

import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { api } from "@/lib/api-client";
import { Card, Badge, Button, KpiCard, Tabs, PageSkeleton, useToast } from "@/components/ui";
import { formatCurrency } from "@/lib/utils";

interface Overview {
  total_spend: number;
  total_impressions: number;
  total_clicks: number;
  avg_ctr: number;
  avg_cpc: number;
  avg_cpm: number;
  active_campaigns: number;
}

interface CampaignRow {
  campaign_id: string;
  campaign_name: string;
  campaign_status: string;
  spend: number;
  impressions: number;
  clicks: number;
  ctr: number;
  cpc: number;
  cpm: number;
}

interface Insight {
  type: string;
  field: string;
  message: string;
}

const TAB_OVERVIEW = "overview";
const TAB_CAMPAIGNS = "campaigns";
const TAB_INSIGHTS = "insights";

export default function MarketingPage() {
  const { toast } = useToast();
  const queryClient = useQueryClient();
  const [tab, setTab] = useState(TAB_OVERVIEW);

  const token = typeof window !== "undefined" ? localStorage.getItem("access_token") : null;

  const { data: fbConfig } = useQuery<{ mode: string }>({
    queryKey: ["facebook-config"],
    queryFn: () => api.get("/facebook/config"),
    enabled: !!token,
  });

  const isMock = fbConfig?.mode === "mock";

  const { data: overview, isLoading: overviewLoading } = useQuery<Overview>({
    queryKey: ["facebook-overview"],
    queryFn: () => api.get("/facebook/overview"),
    enabled: !!token,
  });

  const { data: campaigns, isLoading: campaignsLoading } = useQuery<CampaignRow[]>({
    queryKey: ["facebook-campaigns"],
    queryFn: () => api.get("/facebook/campaigns"),
    enabled: !!token,
  });

  const { data: insights, isLoading: insightsLoading } = useQuery<Insight[]>({
    queryKey: ["facebook-insights"],
    queryFn: () => api.get("/facebook/insights"),
    enabled: !!token,
  });

  const syncMutation = useMutation({
    mutationFn: () => api.post("/facebook/sync", {}),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["facebook-overview"] });
      queryClient.invalidateQueries({ queryKey: ["facebook-campaigns"] });
      queryClient.invalidateQueries({ queryKey: ["facebook-insights"] });
      toast("Sync completed", "success");
    },
    onError: (err: Error) => toast(err.message, "error"),
  });

  const statusVariant: Record<string, "success" | "warning" | "danger" | "default"> = {
    ACTIVE: "success",
    PAUSED: "warning",
    DELETED: "danger",
  };

  return (
    <div className="space-y-6 animate-fade-in">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="font-display text-2xl sm:text-3xl font-extrabold">📈 Marketing</h1>
          <p className="text-[rgb(var(--color-text-secondary))] mt-1 text-sm">Facebook Ads performance</p>
          {isMock && (
            <span className="mt-2 inline-block" title="Data is simulated for development purposes.">
              <Badge variant="warning">🟡 Mock Data</Badge>
            </span>
          )}
        </div>
        <Button onClick={() => syncMutation.mutate()} loading={syncMutation.isPending}>
          Sync Now
        </Button>
      </div>

      <Tabs
        tabs={[
          { id: TAB_OVERVIEW, label: "Overview" },
          { id: TAB_CAMPAIGNS, label: "Campaigns" },
          { id: TAB_INSIGHTS, label: "Insights" },
        ]}
        active={tab}
        onChange={setTab}
      />

      {tab === TAB_OVERVIEW && (
        overviewLoading ? <PageSkeleton /> : overview ? (
          <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 gap-4">
            <KpiCard icon="💰" label="Total Spend" value={formatCurrency(overview.total_spend)} />
            <KpiCard icon="👁️" label="Impressions" value={overview.total_impressions.toLocaleString()} />
            <KpiCard icon="👆" label="Clicks" value={overview.total_clicks.toLocaleString()} />
            <KpiCard icon="📊" label="CTR" value={`${overview.avg_ctr}%`} />
            <KpiCard icon="💵" label="CPC" value={formatCurrency(overview.avg_cpc)} />
            <KpiCard icon="📈" label="CPM" value={formatCurrency(overview.avg_cpm)} />
            <KpiCard icon="🏆" label="Active Campaigns" value={String(overview.active_campaigns)} />
          </div>
        ) : (
          <p className="text-[rgb(var(--color-text-secondary))] py-8 text-center">No data — connect Facebook Ads in Settings</p>
        )
      )}

      {tab === TAB_CAMPAIGNS && (
        campaignsLoading ? <PageSkeleton /> : campaigns && campaigns.length > 0 ? (
          <Card>
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b border-[rgb(var(--color-border))]">
                    <th className="text-right py-3 px-3 font-semibold text-xs text-[rgb(var(--color-text-secondary))]">Campaign</th>
                    <th className="text-right py-3 px-3 font-semibold text-xs text-[rgb(var(--color-text-secondary))]">Status</th>
                    <th className="text-right py-3 px-3 font-semibold text-xs text-[rgb(var(--color-text-secondary))]">Spend</th>
                    <th className="text-right py-3 px-3 font-semibold text-xs text-[rgb(var(--color-text-secondary))]">CTR</th>
                    <th className="text-right py-3 px-3 font-semibold text-xs text-[rgb(var(--color-text-secondary))]">CPC</th>
                    <th className="text-right py-3 px-3 font-semibold text-xs text-[rgb(var(--color-text-secondary))]">Impressions</th>
                  </tr>
                </thead>
                <tbody>
                  {campaigns.map((c) => (
                    <tr key={c.campaign_id} className="border-b border-[rgb(var(--color-border))] last:border-0">
                      <td className="py-3 px-3 font-semibold">{c.campaign_name}</td>
                      <td className="py-3 px-3">
                        <Badge variant={statusVariant[c.campaign_status] || "default"}>{c.campaign_status}</Badge>
                      </td>
                      <td className="py-3 px-3">{formatCurrency(c.spend)}</td>
                      <td className="py-3 px-3">{c.ctr}%</td>
                      <td className="py-3 px-3">{formatCurrency(c.cpc)}</td>
                      <td className="py-3 px-3">{c.impressions.toLocaleString()}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </Card>
        ) : (
          <p className="text-[rgb(var(--color-text-secondary))] py-8 text-center">No campaign data — sync to fetch data</p>
        )
      )}

      {tab === TAB_INSIGHTS && (
        insightsLoading ? <PageSkeleton /> : insights && insights.length > 0 ? (
          <div className="space-y-3">
            {insights.map((insight, idx) => {
              const colors: Record<string, string> = {
                warning: "border-[rgb(var(--color-warning))] bg-amber-50",
                positive: "border-[rgb(var(--color-success))] bg-green-50",
                info: "border-[rgb(var(--color-accent))] bg-blue-50",
              };
              const icons: Record<string, string> = {
                warning: "⚠️",
                positive: "✅",
                info: "💡",
              };
              return (
                <div
                  key={idx}
                  className={`p-4 rounded-xl border-r-4 ${colors[insight.type] || colors.info}`}
                >
                  <p className="text-sm font-semibold">
                    <span className="mr-2">{icons[insight.type] || "💡"}</span>
                    {insight.message}
                  </p>
                </div>
              );
            })}
          </div>
        ) : (
          <p className="text-[rgb(var(--color-text-secondary))] py-8 text-center">No insights yet</p>
        )
      )}
    </div>
  );
}
