"use client";

import { useState } from "react";
import { Button, Input, useToast, Modal, ConfirmDialog, PageHeader, PageSkeleton, Toggle, EmptyState } from "@/components/ui";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { api } from "@/lib/api-client";
import { useTranslations } from "next-intl";

interface Provider {
  id: string;
  name: string;
  code: string;
  api_url: string;
  api_key: string;
  is_active: boolean;
}

export default function ShippingPage() {
  const t = useTranslations("shipping");
  const queryClient = useQueryClient();
  const { toast } = useToast();
  const [modalOpen, setModalOpen] = useState(false);
  const [editing, setEditing] = useState<Provider | null>(null);
  const [deleteTarget, setDeleteTarget] = useState<Provider | null>(null);
  const token = typeof window !== "undefined" ? localStorage.getItem("access_token") : null;

  const { data: providers, isLoading } = useQuery<Provider[]>({
    queryKey: ["shipping-providers"],
    queryFn: () => api.get("/shipping/providers"),
    enabled: !!token,
  });

  function openCreate() {
    setEditing(null);
    setModalOpen(true);
  }

  function openEdit(p: Provider) {
    setEditing(p);
    setModalOpen(true);
  }

  return (
    <div className="space-y-6 animate-fade-in">
      <PageHeader
        title={t("title")}
        description={t("subtitle")}
        actions={<Button onClick={openCreate}>{t("add_provider")}</Button>}
      />

      {isLoading ? (
        <PageSkeleton />
      ) : !providers || providers.length === 0 ? (
        <EmptyState
          icon="🚚"
          title={t("empty.title")}
          description={t("empty.description")}
          actionLabel={t("add_provider")}
          onAction={openCreate}
        />
      ) : (
        <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-4">
          {providers.map((provider) => (
            <ProviderCard
              key={provider.id}
              provider={provider}
              onEdit={() => openEdit(provider)}
              onDelete={() => setDeleteTarget(provider)}
            />
          ))}
        </div>
      )}

      <ProviderFormModal
        isOpen={modalOpen}
        onClose={() => { setModalOpen(false); setEditing(null); }}
        provider={editing}
      />

      <ConfirmDialog
        isOpen={!!deleteTarget}
        onClose={() => setDeleteTarget(null)}
        onConfirm={async () => {
          if (!deleteTarget) return;
          try {
            await api.delete(`/shipping/providers/${deleteTarget.id}`);
            queryClient.invalidateQueries({ queryKey: ["shipping-providers"] });
            toast(t("deleted_success"), "success");
          } catch (err: any) {
            toast(err.message, "error");
          }
          setDeleteTarget(null);
        }}
        title={t("delete.title")}
        message={t("delete.message")}
        confirmLabel={t("actions.confirm_delete")}
        variant="danger"
      />
    </div>
  );
}

function ProviderCard({ provider, onEdit, onDelete }: { provider: Provider; onEdit: () => void; onDelete: () => void }) {
  const t = useTranslations("shipping");
  const queryClient = useQueryClient();
  const { toast } = useToast();

  const toggleMutation = useMutation({
    mutationFn: () =>
      api.put(`/shipping/providers/${provider.id}`, { ...provider, is_active: !provider.is_active }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["shipping-providers"] });
      toast(provider.is_active ? "Provider deactivated" : "Provider activated", "success");
    },
    onError: (err: Error) => toast(err.message, "error"),
  });

  const providerColors: Record<string, string> = {
    yalidine: "from-blue-500 to-blue-700",
    "zr-express": "from-emerald-500 to-emerald-700",
  };

  return (
    <div className="group relative bg-[rgb(var(--color-surface))] border border-[rgb(var(--color-border))] rounded-xl p-5 transition-all duration-200 hover:shadow-md hover:-translate-y-0.5">
      <div className="flex items-start justify-between mb-4">
        <div className={`w-10 h-10 rounded-xl flex items-center justify-center text-white text-sm font-display font-bold bg-gradient-to-br ${providerColors[provider.code] || "from-[rgb(var(--color-accent))] to-[rgb(var(--color-navy-700))]"}`}>
          {provider.name.charAt(0)}
        </div>
        <Toggle
          checked={provider.is_active}
          onChange={() => toggleMutation.mutate()}
          size="sm"
        />
      </div>
      <h3 className="font-display font-bold text-sm mb-0.5">{provider.name}</h3>
      <p className="text-xs text-[rgb(var(--color-text-secondary))] font-mono mb-3">{provider.code}</p>
      <div className="flex items-center gap-2 opacity-0 group-hover:opacity-100 transition-opacity">
        <Button variant="ghost" size="sm" onClick={onEdit}>{t("actions.edit")}</Button>
        <Button variant="ghost" size="sm" onClick={onDelete} className="!text-[rgb(var(--color-danger))]">{t("actions.delete")}</Button>
      </div>
    </div>
  );
}

function ProviderFormModal({ isOpen, onClose, provider }: { isOpen: boolean; onClose: () => void; provider: Provider | null }) {
  const queryClient = useQueryClient();
  const { toast } = useToast();
  const t = useTranslations("shipping");
  const [form, setForm] = useState({
    name: provider?.name || "",
    code: provider?.code || "",
    api_url: provider?.api_url || "",
    api_key: provider?.api_key || "",
  });
  const [saving, setSaving] = useState(false);

  function handleChange(key: string, value: string) {
    setForm((prev) => ({ ...prev, [key]: value }));
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setSaving(true);
    try {
      if (provider) {
        await api.put(`/shipping/providers/${provider.id}`, { ...provider, ...form });
        toast(t("updated_success"), "success");
      } else {
        await api.post("/shipping/providers", form);
        toast(t("created_success"), "success");
      }
      queryClient.invalidateQueries({ queryKey: ["shipping-providers"] });
      onClose();
    } catch (err: any) {
      toast(err.message, "error");
    } finally {
      setSaving(false);
    }
  }

  return (
    <Modal isOpen={isOpen} onClose={onClose} title={provider ? t("edit_provider") : t("add_provider")} size="sm">
      <form onSubmit={handleSubmit} className="space-y-4">
        <Input
          label={t("form.name")}
          id="name"
          value={form.name}
          onChange={(e) => handleChange("name", e.target.value)}
          required
          placeholder={t("placeholder.name")}
        />
        <Input
          label={t("form.code")}
          id="code"
          value={form.code}
          onChange={(e) => handleChange("code", e.target.value)}
          required
          placeholder={t("placeholder.code")}
        />
        <Input
          label={t("form.api_url")}
          id="api_url"
          value={form.api_url}
          onChange={(e) => handleChange("api_url", e.target.value)}
          placeholder={t("placeholder.api_url")}
        />
        <Input
          label={t("form.api_key")}
          id="api_key"
          type="password"
          value={form.api_key}
          onChange={(e) => handleChange("api_key", e.target.value)}
          placeholder={t("placeholder.api_key")}
        />
        <div className="flex gap-3 justify-end pt-2">
          <Button variant="secondary" onClick={onClose} disabled={saving}>{t("actions.cancel")}</Button>
          <Button type="submit" loading={saving}>{provider ? t("actions.save") : t("actions.create")}</Button>
        </div>
      </form>
    </Modal>
  );
}
