"use client";

import { Card, CardTitle, Button, Input, Badge, useToast, PageHeader, PageSkeleton, Tabs, Toggle, Modal, ConfirmDialog, EmptyState } from "@/components/ui";
import { useState, useEffect } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { api } from "@/lib/api-client";
import { useTranslations } from "next-intl";
import { formatDate } from "@/lib/utils";

interface Settings {
  currency: string;
  cod_enabled: boolean;
  language: string;
}

interface Provider {
  id: string;
  name: string;
  code: string;
  provider_type: string;
  is_active: boolean;
  last_test_at: string | null;
  last_test_success: boolean | null;
  last_error: string | null;
}

interface GoogleConfig {
  sheet_id: string | null;
  sheet_url: string | null;
  enabled: boolean;
  last_sync_at: string | null;
  last_test_at: string | null;
  last_test_success: boolean | null;
  last_error: string | null;
}

interface FacebookConfig {
  access_token: string | null;
  ad_account_id: string | null;
  enabled: boolean;
  last_sync_at: string | null;
  last_test_at: string | null;
  last_test_success: boolean | null;
  last_error: string | null;
}

interface TestResult {
  success: boolean;
  message: string;
  details?: Record<string, unknown>;
}

interface IntegrationStatus {
  service: string;
  label: string;
  status: string;
  last_sync_at: string | null;
  last_test_at: string | null;
  last_test_success: boolean | null;
  last_error: string | null;
}

interface IntegrationsStatus {
  google_sheets: IntegrationStatus | null;
  facebook_ads: IntegrationStatus | null;
  shipping_providers: { id: string; name: string; code: string; status: string; last_error: string | null }[];
}

const PROVIDER_TYPES = [
  { value: "yalidine", labelKey: "yalidine", fields: ["api_id", "api_token"] },
  { value: "zr_express", labelKey: "zr_express", fields: ["api_key"] },
  { value: "noest", labelKey: "noest", fields: ["username", "password"] },
  { value: "maystro", labelKey: "maystro", fields: ["api_key"] },
  { value: "custom", labelKey: "custom_provider", fields: [] },
];

export default function SettingsPage() {
  const t = useTranslations("settings");
  const queryClient = useQueryClient();
  const { toast } = useToast();
  const [activeTab, setActiveTab] = useState("general");
  const token = typeof window !== "undefined" ? localStorage.getItem("access_token") : null;

  return (
    <div className="space-y-6 animate-fade-in">
      <PageHeader title={t("title")} description={t("subtitle")} />

      <Tabs
        tabs={[
          { id: "general", label: t("general_tab") },
          { id: "shipping", label: t("shipping_tab") },
          { id: "google", label: t("google_tab") },
          { id: "facebook", label: t("facebook_tab") },
          { id: "integrations", label: t("integrations_tab") },
        ]}
        active={activeTab}
        onChange={setActiveTab}
        variant="pills"
      />

      {activeTab === "general" && <GeneralTab />}
      {activeTab === "shipping" && <ShippingProvidersTab />}
      {activeTab === "google" && <GoogleSheetsTab />}
      {activeTab === "facebook" && <FacebookAdsTab />}
      {activeTab === "integrations" && <IntegrationsTab />}
    </div>
  );
}

/* ── General Tab ─────────────────────────────────────── */

function GeneralTab() {
  const t = useTranslations("settings");
  const queryClient = useQueryClient();
  const { toast } = useToast();
  const token = typeof window !== "undefined" ? localStorage.getItem("access_token") : null;

  const { data: settingsData, isLoading } = useQuery<Settings>({
    queryKey: ["tenant-settings"],
    queryFn: () => api.get("/tenant/settings"),
    enabled: !!token,
  });

  const [currency, setCurrency] = useState("DZD");
  const [language, setLanguage] = useState("ar");
  const [codEnabled, setCodEnabled] = useState(true);

  useEffect(() => {
    if (settingsData) {
      setCurrency(settingsData.currency);
      setLanguage(settingsData.language);
      setCodEnabled(settingsData.cod_enabled);
    }
  }, [settingsData]);

  const mutation = useMutation({
    mutationFn: () => api.put("/tenant/settings", { currency, cod_enabled: codEnabled, language }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["tenant-settings"] });
      toast(t("saved"), "success");
    },
    onError: (err: Error) => toast(err.message, "error"),
  });

  if (isLoading) return <PageSkeleton />;

  return (
    <div className="grid md:grid-cols-2 gap-6">
      <Card>
        <CardTitle>{t("general")}</CardTitle>
        <div className="space-y-4 mt-4">
          <Input label={t("currency")} id="currency" value={currency} onChange={(e) => setCurrency(e.target.value)} />
          <div className="space-y-1.5">
            <label className="label">{t("language")}</label>
            <select className="w-full px-3.5 py-2.5 bg-[rgb(var(--color-surface))] border border-[rgb(var(--color-border))] rounded-lg font-body text-sm text-[rgb(var(--color-text))] focus:outline-none focus:border-[rgb(var(--color-accent))]"
              value={language} onChange={(e) => setLanguage(e.target.value)}>
              <option value="ar">العربية</option>
              <option value="fr">Français</option>
              <option value="en">English</option>
            </select>
          </div>
          <Toggle checked={codEnabled} onChange={setCodEnabled} label={t("cod_label")} />
          <div className="pt-4 border-t border-[rgb(var(--color-border))]">
            <Button onClick={() => mutation.mutate()} loading={mutation.isPending}>{t("save")}</Button>
          </div>
        </div>
      </Card>
    </div>
  );
}

/* ── Shipping Providers Tab ──────────────────────────── */

function ShippingProvidersTab() {
  const t = useTranslations("settings");
  const queryClient = useQueryClient();
  const { toast } = useToast();
  const token = typeof window !== "undefined" ? localStorage.getItem("access_token") : null;
  const [modalOpen, setModalOpen] = useState(false);
  const [editing, setEditing] = useState<Provider | null>(null);
  const [deleteTarget, setDeleteTarget] = useState<Provider | null>(null);

  const { data: providers, isLoading } = useQuery<Provider[]>({
    queryKey: ["shipping-providers"],
    queryFn: () => api.get("/shipping/providers"),
    enabled: !!token,
  });

  function openCreate() { setEditing(null); setModalOpen(true); }
  function openEdit(p: Provider) { setEditing(p); setModalOpen(true); }

  return (
    <div className="space-y-4">
      <div className="flex justify-end">
        <Button onClick={openCreate}>{t("add_provider")}</Button>
      </div>
      {isLoading ? <PageSkeleton /> : !providers || providers.length === 0 ? (
        <EmptyState icon="🚚" title={t("no_providers")} actionLabel={t("add_provider")} onAction={openCreate} />
      ) : (
        <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-4">
          {providers.map((p) => (
            <ProviderCard key={p.id} provider={p} onEdit={() => openEdit(p)} onDelete={() => setDeleteTarget(p)} />
          ))}
        </div>
      )}
      <ProviderFormModal isOpen={modalOpen} onClose={() => { setModalOpen(false); setEditing(null); }} provider={editing} />
      <ConfirmDialog
        isOpen={!!deleteTarget} onClose={() => setDeleteTarget(null)}
        onConfirm={async () => {
          if (!deleteTarget) return;
          try {
            await api.delete(`/shipping/providers/${deleteTarget.id}`);
            queryClient.invalidateQueries({ queryKey: ["shipping-providers"] });
            toast(t("provider_deleted"), "success");
          } catch (err: any) { toast(err.message, "error"); }
          setDeleteTarget(null);
        }}
        title={t("edit_provider")} message={t("confirm_delete_provider")} confirmLabel={t("edit_provider")} variant="danger"
      />
    </div>
  );
}

function ProviderCard({ provider, onEdit, onDelete }: { provider: Provider; onEdit: () => void; onDelete: () => void }) {
  const t = useTranslations("settings");
  const queryClient = useQueryClient();
  const { toast } = useToast();
  const [testing, setTesting] = useState(false);

  const toggleMutation = useMutation({
    mutationFn: () => api.put(`/shipping/providers/${provider.id}`, { is_active: !provider.is_active }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["shipping-providers"] });
      toast(provider.is_active ? "Deactivated" : "Activated", "success");
    },
    onError: (err: Error) => toast(err.message, "error"),
  });

  const providerColors: Record<string, string> = {
    yalidine: "from-blue-500 to-blue-700",
    "zr_express": "from-emerald-500 to-emerald-700",
    noest: "from-purple-500 to-purple-700",
    maystro: "from-orange-500 to-orange-700",
  };

  async function testConnection() {
    setTesting(true);
    try {
      const res = await api.post<TestResult>(`/integrations/shipping/${provider.id}/test`, {});
      toast(res.message, res.success ? "success" : "error");
      queryClient.invalidateQueries({ queryKey: ["shipping-providers"] });
    } catch (err: any) { toast(err.message, "error"); }
    setTesting(false);
  }

  const statusBadge = () => {
    if (provider.last_error) return <Badge variant="danger">{t("status_error")}</Badge>;
    if (provider.last_test_success) return <Badge variant="success">{t("status_connected")}</Badge>;
    if (provider.is_active) return <Badge variant="warning">{t("status_disabled")}</Badge>;
    return <Badge variant="default">{t("status_not_configured")}</Badge>;
  };

  return (
    <div className="bg-[rgb(var(--color-surface))] border border-[rgb(var(--color-border))] rounded-xl p-5 transition-all duration-200 hover:shadow-md hover:-translate-y-0.5">
      <div className="flex items-start justify-between mb-3">
        <div className={`w-10 h-10 rounded-xl flex items-center justify-center text-white text-sm font-display font-bold bg-gradient-to-br ${providerColors[provider.code] || "from-[rgb(var(--color-accent))] to-[rgb(var(--color-navy-700))]"}`}>
          {provider.name.charAt(0)}
        </div>
        <Toggle checked={provider.is_active} onChange={() => toggleMutation.mutate()} size="sm" />
      </div>
      <h3 className="font-display font-bold text-sm mb-0.5">{provider.name}</h3>
      <p className="text-xs text-[rgb(var(--color-text-secondary))] font-mono mb-3">{provider.code}</p>
      <div className="flex items-center gap-2 mb-3">{statusBadge()}</div>
      {provider.last_error && <p className="text-xs text-[rgb(var(--color-danger))] mb-2 truncate">{provider.last_error}</p>}
      <div className="flex items-center gap-2">
        <Button variant="ghost" size="sm" onClick={onEdit}>{t("edit_provider")}</Button>
        <Button variant="ghost" size="sm" onClick={testConnection} loading={testing}>{t("test_connection")}</Button>
        <Button variant="ghost" size="sm" onClick={onDelete} className="!text-[rgb(var(--color-danger))]">{t("edit_provider")}</Button>
      </div>
    </div>
  );
}

function ProviderFormModal({ isOpen, onClose, provider }: { isOpen: boolean; onClose: () => void; provider: Provider | null }) {
  const queryClient = useQueryClient();
  const { toast } = useToast();
  const t = useTranslations("settings");
  const [type, setType] = useState(provider?.provider_type || "yalidine");
  const [credentials, setCredentials] = useState<Record<string, string>>({});
  const [name, setName] = useState(provider?.name || "");
  const [code, setCode] = useState(provider?.code || "");
  const [saving, setSaving] = useState(false);

  const providerFields = PROVIDER_TYPES.find((pt) => pt.value === type)?.fields || [];

  function handleCredentialChange(key: string, value: string) {
    setCredentials((prev) => ({ ...prev, [key]: value }));
  }

  useEffect(() => {
    if (!provider) {
      setType("yalidine");
      setCredentials({});
      setName("");
      setCode("");
    } else {
      setType(provider.provider_type);
      setName(provider.name);
      setCode(provider.code);
    }
  }, [provider, isOpen]);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setSaving(true);
    try {
      const body = { name, code, provider_type: type, credentials };
      if (provider) {
        await api.put(`/shipping/providers/${provider.id}`, body);
        toast(t("provider_updated"), "success");
      } else {
        await api.post("/shipping/providers", body);
        toast(t("provider_created"), "success");
      }
      queryClient.invalidateQueries({ queryKey: ["shipping-providers"] });
      onClose();
    } catch (err: any) { toast(err.message, "error"); }
    setSaving(false);
  }

  return (
    <Modal isOpen={isOpen} onClose={onClose} title={provider ? t("edit_provider") : t("add_provider")} size="sm">
      <form onSubmit={handleSubmit} className="space-y-4">
        <Input label={t("edit_provider")} id="name" value={name} onChange={(e) => setName(e.target.value)} required placeholder="e.g. Yalidine" />
        <Input label="Code" id="code" value={code} onChange={(e) => setCode(e.target.value)} required placeholder="e.g. yalidine" />
        <div className="space-y-1.5">
          <label className="label">{t("provider_type")}</label>
          <select className="w-full px-3.5 py-2.5 bg-[rgb(var(--color-surface))] border border-[rgb(var(--color-border))] rounded-lg font-body text-sm text-[rgb(var(--color-text))] focus:outline-none focus:border-[rgb(var(--color-accent))]"
            value={type} onChange={(e) => setType(e.target.value)}>
            {PROVIDER_TYPES.map((pt) => (
              <option key={pt.value} value={pt.value}>{t(pt.labelKey)}</option>
            ))}
          </select>
        </div>
        {providerFields.map((field) => (
          <Input key={field} label={t(field)} id={field} type={field === "password" ? "password" : "text"}
            value={credentials[field] || ""} onChange={(e) => handleCredentialChange(field, e.target.value)} placeholder="••••••••" required />
        ))}
        <div className="flex gap-3 justify-end pt-2">
          <Button variant="secondary" onClick={onClose} disabled={saving}>{t("edit_provider")}</Button>
          <Button type="submit" loading={saving}>{provider ? t("edit_provider") : t("add_provider")}</Button>
        </div>
      </form>
    </Modal>
  );
}

/* ── Google Sheets Tab ───────────────────────────────── */

function GoogleSheetsTab() {
  const t = useTranslations("settings");
  const queryClient = useQueryClient();
  const { toast } = useToast();
  const token = typeof window !== "undefined" ? localStorage.getItem("access_token") : null;
  const [sheetUrl, setSheetUrl] = useState("");
  const [testing, setTesting] = useState(false);

  const { data: config, isLoading } = useQuery<GoogleConfig>({
    queryKey: ["google-config"],
    queryFn: () => api.get("/integrations/google/config"),
    enabled: !!token,
  });

  const testMutation = useMutation({
    mutationFn: () => api.post<TestResult>("/integrations/google/test", { sheet_url: sheetUrl || undefined }),
    onSuccess: (res) => {
      toast(res.message, res.success ? "success" : "error");
      queryClient.invalidateQueries({ queryKey: ["google-config"] });
    },
    onError: (err: Error) => toast(err.message, "error"),
  });

  const saveMutation = useMutation({
    mutationFn: () => api.post("/integrations/google/configure", { sheet_url: sheetUrl, enable_sync: true }),
    onSuccess: () => {
      toast(t("config_saved"), "success");
      queryClient.invalidateQueries({ queryKey: ["google-config"] });
    },
    onError: (err: Error) => toast(err.message, "error"),
  });

  const syncMutation = useMutation({
    mutationFn: () => api.post("/google/sync", {}),
    onSuccess: () => {
      toast("Sync completed", "success");
      queryClient.invalidateQueries({ queryKey: ["google-config"] });
    },
    onError: (err: Error) => toast(err.message, "error"),
  });

  useEffect(() => {
    if (config?.sheet_url) setSheetUrl(config.sheet_url);
  }, [config]);

  if (isLoading) return <PageSkeleton />;

  const canEnable = config?.last_test_success === true;

  return (
    <div className="grid md:grid-cols-2 gap-6">
      <Card>
        <CardTitle>Google Sheets</CardTitle>
        <div className="space-y-4 mt-4">
          <Input label={t("sheet_url")} id="sheet_url" value={sheetUrl}
            onChange={(e) => setSheetUrl(e.target.value)} placeholder={t("sheet_url_placeholder")} />
          <div className="flex gap-2">
            <Button onClick={() => testMutation.mutate()} loading={testMutation.isPending} variant="secondary">{t("test_connection")}</Button>
            <Button onClick={() => saveMutation.mutate()} loading={saveMutation.isPending} disabled={!canEnable}>{t("enable_sync")}</Button>
          </div>
          {!canEnable && config?.sheet_id && (
            <p className="text-xs text-[rgb(var(--color-text-secondary))]">Test connection first before enabling sync</p>
          )}
        </div>
      </Card>
      <Card>
        <CardTitle>Status</CardTitle>
        <div className="space-y-3 mt-4">
          <StatusRow label={t("status")} value={
            config?.last_test_success ? <Badge variant="success">{t("status_connected")}</Badge> :
            config?.last_error ? <Badge variant="danger">{t("status_error")}</Badge> :
            config?.sheet_id ? <Badge variant="warning">{t("status_disabled")}</Badge> :
            <Badge variant="default">{t("status_not_configured")}</Badge>
          } />
          <StatusRow label={t("last_sync")} value={config?.last_sync_at ? formatDate(config.last_sync_at) : "—"} />
          <StatusRow label={t("last_test")} value={config?.last_test_at ? formatDate(config.last_test_at) : "—"} />
          <StatusRow label={t("last_error")} value={config?.last_error || "—"} />
          <div className="pt-4 border-t border-[rgb(var(--color-border))]">
            <Button onClick={() => syncMutation.mutate()} loading={syncMutation.isPending} variant="secondary" disabled={!config?.enabled}>{t("sync_now")}</Button>
          </div>
        </div>
      </Card>
    </div>
  );
}

/* ── Facebook Ads Tab ────────────────────────────────── */

function FacebookAdsTab() {
  const t = useTranslations("settings");
  const queryClient = useQueryClient();
  const { toast } = useToast();
  const token = typeof window !== "undefined" ? localStorage.getItem("access_token") : null;
  const [accessToken, setAccessToken] = useState("");
  const [adAccountId, setAdAccountId] = useState("");

  const { data: config, isLoading } = useQuery<FacebookConfig>({
    queryKey: ["facebook-config"],
    queryFn: () => api.get("/integrations/facebook/config"),
    enabled: !!token,
  });

  const testMutation = useMutation({
    mutationFn: () => api.post<TestResult>("/integrations/facebook/test", {
      access_token: accessToken || undefined,
      ad_account_id: adAccountId || undefined,
    }),
    onSuccess: (res) => {
      toast(res.message, res.success ? "success" : "error");
      queryClient.invalidateQueries({ queryKey: ["facebook-config"] });
    },
    onError: (err: Error) => toast(err.message, "error"),
  });

  const saveMutation = useMutation({
    mutationFn: () => api.post("/integrations/facebook/configure", {
      access_token: accessToken,
      ad_account_id: adAccountId,
      enable_sync: true,
    }),
    onSuccess: () => {
      toast(t("config_saved"), "success");
      queryClient.invalidateQueries({ queryKey: ["facebook-config"] });
    },
    onError: (err: Error) => toast(err.message, "error"),
  });

  useEffect(() => {
    if (config?.ad_account_id) setAdAccountId(config.ad_account_id);
  }, [config]);

  if (isLoading) return <PageSkeleton />;

  const canEnable = config?.last_test_success === true;

  return (
    <div className="grid md:grid-cols-2 gap-6">
      <Card>
        <CardTitle>Facebook Ads</CardTitle>
        <div className="space-y-4 mt-4">
          <Input label={t("facebook_access_token")} id="access_token" type="password" value={accessToken}
            onChange={(e) => setAccessToken(e.target.value)} placeholder="••••••••" />
          <Input label={t("facebook_ad_account_id")} id="ad_account_id" value={adAccountId}
            onChange={(e) => setAdAccountId(e.target.value)} placeholder="e.g. 123456789" />
          <div className="flex gap-2">
            <Button onClick={() => testMutation.mutate()} loading={testMutation.isPending} variant="secondary">{t("test_connection")}</Button>
            <Button onClick={() => saveMutation.mutate()} loading={saveMutation.isPending} disabled={!canEnable}>{t("enable_sync")}</Button>
          </div>
          {!canEnable && config?.ad_account_id && (
            <p className="text-xs text-[rgb(var(--color-text-secondary))]">Test connection first before enabling sync</p>
          )}
        </div>
      </Card>
      <Card>
        <CardTitle>Status</CardTitle>
        <div className="space-y-3 mt-4">
          <StatusRow label={t("status")} value={
            config?.last_test_success ? <Badge variant="success">{t("status_connected")}</Badge> :
            config?.last_error ? <Badge variant="danger">{t("status_error")}</Badge> :
            config?.ad_account_id ? <Badge variant="warning">{t("status_disabled")}</Badge> :
            <Badge variant="default">{t("status_not_configured")}</Badge>
          } />
          <StatusRow label={t("last_sync")} value={config?.last_sync_at ? formatDate(config.last_sync_at) : "—"} />
          <StatusRow label={t("last_test")} value={config?.last_test_at ? formatDate(config.last_test_at) : "—"} />
          <StatusRow label={t("last_error")} value={config?.last_error || "—"} />
        </div>
      </Card>
    </div>
  );
}

/* ── Integrations Tab ────────────────────────────────── */

function IntegrationsTab() {
  const t = useTranslations("settings");
  const token = typeof window !== "undefined" ? localStorage.getItem("access_token") : null;

  const { data: status, isLoading } = useQuery<IntegrationsStatus>({
    queryKey: ["integrations-status"],
    queryFn: () => api.get("/integrations/status"),
    enabled: !!token,
  });

  if (isLoading) return <PageSkeleton />;

  const services = [
    status?.google_sheets,
    status?.facebook_ads,
    ...(status?.shipping_providers || []).map((sp) => ({
      service: sp.code,
      label: sp.name,
      status: sp.status,
      last_error: sp.last_error,
    })),
  ].filter(Boolean);

  const statusBadge = (s: string) => {
    const map: Record<string, "success" | "danger" | "warning" | "default"> = {
      connected: "success",
      error: "danger",
      disabled: "warning",
    };
    return <Badge variant={map[s] || "default"}>{t(`status_${s}` as any) || s}</Badge>;
  };

  return (
    <Card>
      <CardTitle>{t("integrations_status_title")}</CardTitle>
      <p className="text-sm text-[rgb(var(--color-text-secondary))] mb-4">{t("integrations_status_desc")}</p>
      <div className="overflow-x-auto">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-[rgb(var(--color-border))]">
              <th className="text-right py-3 px-3 font-semibold text-xs text-[rgb(var(--color-text-secondary))]">{t("service")}</th>
              <th className="text-right py-3 px-3 font-semibold text-xs text-[rgb(var(--color-text-secondary))]">{t("status")}</th>
              <th className="text-right py-3 px-3 font-semibold text-xs text-[rgb(var(--color-text-secondary))]">{t("last_error")}</th>
            </tr>
          </thead>
          <tbody>
            {services.map((svc: any) => (
              <tr key={svc.service} className="border-b border-[rgb(var(--color-border))] last:border-0">
                <td className="py-3 px-3 font-semibold">{svc.label}</td>
                <td className="py-3 px-3">{statusBadge(svc.status)}</td>
                <td className="py-3 px-3 text-xs text-[rgb(var(--color-text-secondary))]">{svc.last_error || "—"}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </Card>
  );
}

/* ── Shared helpers ──────────────────────────────────── */

function StatusRow({ label, value }: { label: string; value: React.ReactNode }) {
  return (
    <div className="flex items-center justify-between py-1">
      <span className="text-sm text-[rgb(var(--color-text-secondary))]">{label}</span>
      <span className="text-sm font-semibold">{value}</span>
    </div>
  );
}
