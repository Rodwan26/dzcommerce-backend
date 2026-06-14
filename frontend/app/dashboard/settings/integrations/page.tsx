"use client";

import { Card, CardTitle, Badge, Button, PageHeader, PageSkeleton } from "@/components/ui";
import { useQuery } from "@tanstack/react-query";
import { api } from "@/lib/api-client";
import { useTranslations } from "next-intl";
import { formatDate } from "@/lib/utils";
import { useRouter } from "next/navigation";

interface IntegrationStatus {
  service: string;
  label: string;
  status: string;
  last_sync_at: string | null;
  next_sync_at: string | null;
  last_test_at: string | null;
  last_test_success: boolean | null;
  last_error: string | null;
}

interface ProviderStatus {
  id: string;
  name: string;
  code: string;
  status: string;
  last_test_at: string | null;
  last_test_success: boolean | null;
  last_error: string | null;
}

interface IntegrationsStatus {
  google_sheets: IntegrationStatus | null;
  facebook_ads: IntegrationStatus | null;
  shipping_providers: ProviderStatus[];
}

const SERVICE_CONFIG_PATHS: Record<string, string> = {
  google_sheets: "/dashboard/settings?tab=google",
  facebook_ads: "/dashboard/settings?tab=facebook",
};

export default function IntegrationsPage() {
  const t = useTranslations("settings");
  const router = useRouter();
  const token = typeof window !== "undefined" ? localStorage.getItem("access_token") : null;

  const { data, isLoading } = useQuery<IntegrationsStatus>({
    queryKey: ["integrations-status"],
    queryFn: () => api.get("/integrations/status"),
    enabled: !!token,
  });

  const statusVariant: Record<string, "success" | "danger" | "warning" | "default"> = {
    connected: "success",
    error: "danger",
    disabled: "warning",
    not_configured: "default",
  };

  const statusLabel: Record<string, string> = {
    connected: t("status_connected"),
    error: t("status_error"),
    disabled: t("status_disabled"),
    not_configured: t("status_not_configured"),
  };

  if (isLoading) return <PageSkeleton />;

  return (
    <div className="space-y-6 animate-fade-in">
      <PageHeader title={t("integrations_status_title")} description={t("integrations_status_desc")} />

      <Card>
        <CardTitle>{t("integrations_status_title")}</CardTitle>
        <div className="overflow-x-auto mt-4">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-[rgb(var(--color-border))]">
                <th className="text-right py-3 px-3 font-semibold text-xs text-[rgb(var(--color-text-secondary))]">{t("service")}</th>
                <th className="text-right py-3 px-3 font-semibold text-xs text-[rgb(var(--color-text-secondary))]">{t("status")}</th>
                <th className="text-right py-3 px-3 font-semibold text-xs text-[rgb(var(--color-text-secondary))]">{t("last_sync")}</th>
                <th className="text-right py-3 px-3 font-semibold text-xs text-[rgb(var(--color-text-secondary))]">{t("last_test")}</th>
                <th className="text-right py-3 px-3 font-semibold text-xs text-[rgb(var(--color-text-secondary))]">{t("last_error")}</th>
                <th className="text-right py-3 px-3 font-semibold text-xs text-[rgb(var(--color-text-secondary))]"></th>
              </tr>
            </thead>
            <tbody>
              {data?.google_sheets && (
                <IntegrationRow
                  label={data.google_sheets.label}
                  status={data.google_sheets.status}
                  lastSync={data.google_sheets.last_sync_at}
                  lastTest={data.google_sheets.last_test_at}
                  lastError={data.google_sheets.last_error}
                  statusVariant={statusVariant}
                  statusLabel={statusLabel}
                  onConfigure={() => router.push(SERVICE_CONFIG_PATHS.google_sheets)}
                />
              )}
              {data?.facebook_ads && (
                <IntegrationRow
                  label={data.facebook_ads.label}
                  status={data.facebook_ads.status}
                  lastSync={data.facebook_ads.last_sync_at}
                  lastTest={data.facebook_ads.last_test_at}
                  lastError={data.facebook_ads.last_error}
                  statusVariant={statusVariant}
                  statusLabel={statusLabel}
                  onConfigure={() => router.push(SERVICE_CONFIG_PATHS.facebook_ads)}
                />
              )}
              {data?.shipping_providers?.map((sp) => (
                <IntegrationRow
                  key={sp.id}
                  label={sp.name}
                  status={sp.status}
                  lastSync={null}
                  lastTest={sp.last_test_at}
                  lastError={sp.last_error}
                  statusVariant={statusVariant}
                  statusLabel={statusLabel}
                  onConfigure={() => router.push("/dashboard/settings?tab=shipping")}
                />
              ))}
            </tbody>
          </table>
        </div>
      </Card>
    </div>
  );
}

function IntegrationRow({
  label, status, lastSync, lastTest, lastError, statusVariant, statusLabel, onConfigure,
}: {
  label: string; status: string; lastSync: string | null; lastTest: string | null; lastError: string | null;
  statusVariant: Record<string, "success" | "danger" | "warning" | "default">;
  statusLabel: Record<string, string>; onConfigure: () => void;
}) {
  return (
    <tr className="border-b border-[rgb(var(--color-border))] last:border-0">
      <td className="py-3 px-3 font-semibold">{label}</td>
      <td className="py-3 px-3"><Badge variant={statusVariant[status] || "default"}>{statusLabel[status] || status}</Badge></td>
      <td className="py-3 px-3 text-xs text-[rgb(var(--color-text-secondary))]">{lastSync ? formatDate(lastSync) : "—"}</td>
      <td className="py-3 px-3 text-xs text-[rgb(var(--color-text-secondary))]">{lastTest ? formatDate(lastTest) : "—"}</td>
      <td className="py-3 px-3 text-xs text-[rgb(var(--color-danger))] max-w-[200px] truncate">{lastError || "—"}</td>
      <td className="py-3 px-3"><Button variant="ghost" size="sm" onClick={onConfigure}>{statusLabel["not_configured"] || "Configure"}</Button></td>
    </tr>
  );
}
