"use client";

import { useParams, useRouter } from "next/navigation";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { api } from "@/lib/api-client";
import { Card, CardTitle, Badge, Button, Select, useToast, PageSkeleton } from "@/components/ui";
import { formatDateShort, formatCurrency } from "@/lib/utils";
import { useTranslations } from "next-intl";
import { useState } from "react";

interface OrderItem {
  id: string;
  product_id: string | null;
  quantity: number;
  unit_price: number;
}

interface ShipmentBrief {
  id: string;
  provider_name: string;
  tracking_code: string | null;
  status: string;
}

interface ShipmentEvent {
  id: string;
  status: string;
  note: string | null;
  occurred_at: string;
}

interface ShipmentDetail {
  id: string;
  provider_name: string;
  tracking_code: string | null;
  status: string;
  events: ShipmentEvent[];
  label_url: string | null;
}

interface Order {
  id: string;
  user_id: string;
  status: string;
  confirmation_status: string;
  shipping_status: string;
  confirmed_at: string | null;
  total: number;
  created_at: string;
  updated_at: string | null;
  items: OrderItem[];
  shipments: ShipmentBrief[];
}

const confirmationConfig: Record<string, { labelKey: string; variant: "warning" | "success" | "danger" | "default" }> = {
  pending: { labelKey: "confirmation_pending", variant: "warning" },
  confirmed: { labelKey: "confirmation_confirmed", variant: "success" },
  cancelled: { labelKey: "confirmation_cancelled", variant: "danger" },
};

const shippingConfig: Record<string, { labelKey: string; variant: "default" | "info" | "success" | "danger" | "warning" }> = {
  not_sent: { labelKey: "shipping_not_sent", variant: "default" },
  picked_up: { labelKey: "shipping_picked_up", variant: "info" },
  in_transit: { labelKey: "shipping_in_transit", variant: "info" },
  delivered: { labelKey: "shipping_delivered", variant: "success" },
  returned: { labelKey: "shipping_returned", variant: "danger" },
  failed: { labelKey: "shipping_failed", variant: "danger" },
};

const shipmentSteps = ["pending", "picked_up", "in_transit", "delivered", "returned", "failed"];

const shipmentLabels: Record<string, string> = {
  pending: "Pending",
  picked_up: "Picked Up",
  in_transit: "In Transit",
  delivered: "Delivered",
  returned: "Returned",
  failed: "Failed",
};

const shipmentVariants: Record<string, "warning" | "info" | "success" | "danger" | "default"> = {
  pending: "warning",
  picked_up: "info",
  in_transit: "info",
  delivered: "success",
  returned: "danger",
  failed: "danger",
};

export default function OrderDetailPage() {
  const t = useTranslations("orders");
  const params = useParams();
  const router = useRouter();
  const queryClient = useQueryClient();
  const { toast } = useToast();
  const [shippingUpdateValue, setShippingUpdateValue] = useState("");
  const token = typeof window !== "undefined" ? localStorage.getItem("access_token") : null;

  const { data: order, isLoading } = useQuery<Order>({
    queryKey: ["order", params.id],
    queryFn: () => api.get(`/orders/${params.id}`),
    enabled: !!token,
  });

  const shipmentId = order?.shipments?.[0]?.id;
  const { data: shipmentDetail } = useQuery<ShipmentDetail>({
    queryKey: ["shipment", shipmentId],
    queryFn: () => api.get(`/shipping/shipments/${shipmentId}`),
    enabled: !!shipmentId,
  });

  const confirmMutation = useMutation({
    mutationFn: () =>
      api.patch(`/orders/${params.id}/confirmation-status`, { confirmation_status: "confirmed" }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["order", params.id] });
      toast("Order confirmed", "success");
    },
    onError: (err: Error) => toast(err.message, "error"),
  });

  const cancelMutation = useMutation({
    mutationFn: () =>
      api.patch(`/orders/${params.id}/confirmation-status`, { confirmation_status: "cancelled" }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["order", params.id] });
      toast("Order cancelled", "success");
    },
    onError: (err: Error) => toast(err.message, "error"),
  });

  const shippingMutation = useMutation({
    mutationFn: (status: string) =>
      api.patch(`/orders/${params.id}/shipping-status`, { shipping_status: status }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["order", params.id] });
      setShippingUpdateValue("");
      toast("Shipping status updated", "success");
    },
    onError: (err: Error) => toast(err.message, "error"),
  });

  if (isLoading) return <PageSkeleton />;

  if (!order) {
    return (
      <div className="flex items-center justify-center min-h-[50vh]">
        <p className="text-[rgb(var(--color-text-secondary))]">{t("order_not_found")}</p>
      </div>
    );
  }

  const confirmCfg = confirmationConfig[order.confirmation_status] || confirmationConfig.pending;
  const shipCfg = shippingConfig[order.shipping_status] || shippingConfig.not_sent;

  return (
    <div className="space-y-6 animate-fade-in">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <button
            onClick={() => router.back()}
            className="flex items-center gap-1 text-sm text-[rgb(var(--color-text-secondary))] hover:text-[rgb(var(--color-text))] transition-colors mb-2"
          >
            <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M15 19l-7-7 7-7" />
            </svg>
            {t("back")}
          </button>
          <h1 className="font-display text-2xl sm:text-3xl font-extrabold">
            {t("title")} <span className="text-[rgb(var(--color-accent))]">#{order.id.slice(0, 8)}</span>
          </h1>
          <p className="text-[rgb(var(--color-text-secondary))] mt-1 text-sm">{formatDateShort(order.created_at)}</p>
        </div>
      </div>

      <div className="grid lg:grid-cols-3 gap-6">
        {/* Left: Order Items */}
        <div className="lg:col-span-2 space-y-6">
          <Card>
            <CardTitle>{t("order_items")}</CardTitle>
            <div className="mt-4 overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b border-[rgb(var(--color-border))]">
                    <th className="text-right py-3 px-3 font-semibold text-xs text-[rgb(var(--color-text-secondary))]">{t("product")}</th>
                    <th className="text-right py-3 px-3 font-semibold text-xs text-[rgb(var(--color-text-secondary))]">{t("qty")}</th>
                    <th className="text-right py-3 px-3 font-semibold text-xs text-[rgb(var(--color-text-secondary))]">{t("price")}</th>
                    <th className="text-right py-3 px-3 font-semibold text-xs text-[rgb(var(--color-text-secondary))]">{t("subtotal")}</th>
                  </tr>
                </thead>
                <tbody>
                  {order.items.map((item) => (
                    <tr key={item.id} className="border-b border-[rgb(var(--color-border))] last:border-0">
                      <td className="py-3 px-3 font-semibold">{item.product_id ? `#${item.product_id.slice(0, 8)}` : "N/A"}</td>
                      <td className="py-3 px-3">{item.quantity}</td>
                      <td className="py-3 px-3">{formatCurrency(item.unit_price)}</td>
                      <td className="py-3 px-3 font-semibold">{formatCurrency(item.quantity * item.unit_price)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
            <div className="flex justify-between items-center mt-4 pt-4 border-t border-[rgb(var(--color-border))]">
              <span className="text-sm text-[rgb(var(--color-text-secondary))]">{t("total")}</span>
              <span className="font-display text-2xl font-extrabold text-[rgb(var(--color-accent))]">{formatCurrency(order.total)}</span>
            </div>
          </Card>
        </div>

        {/* Right: Confirmation + Shipping */}
        <div className="space-y-6">
          {/* Confirmation Section */}
          <Card>
            <CardTitle>{t("table_confirmation")}</CardTitle>
            <div className="mt-4 space-y-4 text-sm">
              <div className="flex justify-between items-center">
                <span className="text-[rgb(var(--color-text-secondary))]">{t("table_status")}</span>
                <Badge variant={confirmCfg.variant}>{t(confirmCfg.labelKey)}</Badge>
              </div>
              {order.confirmed_at && (
                <div className="flex justify-between">
                  <span className="text-[rgb(var(--color-text-secondary))]">{t("confirmed_at")}</span>
                  <span className="font-semibold">{formatDateShort(order.confirmed_at)}</span>
                </div>
              )}
              {order.confirmation_status === "pending" && (
                <div className="flex gap-2 pt-2">
                  <Button
                    size="sm"
                    onClick={() => confirmMutation.mutate()}
                    loading={confirmMutation.isPending}
                    className="flex-1"
                  >
                    {t("confirm_order")}
                  </Button>
                  <Button
                    size="sm"
                    variant="secondary"
                    onClick={() => cancelMutation.mutate()}
                    loading={cancelMutation.isPending}
                    className="flex-1"
                  >
                    {t("cancel_order")}
                  </Button>
                </div>
              )}
            </div>
          </Card>

          {/* Shipping Section */}
          <Card>
            <CardTitle>{t("table_shipping_status")}</CardTitle>
            <div className="mt-4 space-y-4 text-sm">
              <div className="flex justify-between items-center">
                <span className="text-[rgb(var(--color-text-secondary))]">{t("table_status")}</span>
                <Badge variant={shipCfg.variant}>{t(shipCfg.labelKey)}</Badge>
              </div>

              {order.shipments?.[0] && (
                <>
                  <div className="flex justify-between">
                    <span className="text-[rgb(var(--color-text-secondary))]">{t("tracking")}</span>
                    <span className="font-mono text-xs font-semibold">{order.shipments[0].tracking_code || "—"}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-[rgb(var(--color-text-secondary))]">{t("table_shipping")}</span>
                    <span className="font-semibold">{order.shipments[0].provider_name}</span>
                  </div>
                  <div className="flex gap-2 pt-2">
                    <Select
                      value={shippingUpdateValue}
                      onChange={(e) => {
                        const val = e.target.value;
                        setShippingUpdateValue(val);
                        if (val) shippingMutation.mutate(val);
                      }}
                      options={[
                        { value: "", label: t("update_status") },
                        ...Object.entries(shippingConfig).map(([value, cfg]) => ({
                          value,
                          label: t(cfg.labelKey),
                        })),
                      ]}
                      className="flex-1"
                    />
                  </div>

                  {/* Shipment Timeline */}
                  {shipmentDetail && shipmentDetail.events.length > 0 && (
                    <div className="mt-4 pt-4 border-t border-[rgb(var(--color-border))]">
                      <p className="font-semibold text-xs text-[rgb(var(--color-text-secondary))] mb-4 uppercase tracking-wider">{t("timeline")}</p>
                      <div className="space-y-0">
                        {shipmentSteps.map((step, idx) => {
                          const event = shipmentDetail.events.find((e) => e.status === step);
                          const isActive = !!event;
                          const isCurrent = order.shipments[0].status === step;
                          return (
                            <div key={step} className="flex items-start gap-3 relative">
                              <div className="flex flex-col items-center">
                                <div className={`w-3 h-3 rounded-full border-2 shrink-0 z-10 ${
                                  isActive ? "bg-[rgb(var(--color-accent))] border-[rgb(var(--color-accent))]" :
                                  isCurrent ? "border-[rgb(var(--color-accent))] bg-white" :
                                  "bg-[rgb(var(--color-surface))] border-[rgb(var(--color-border))]"
                                }`} />
                                {idx < shipmentSteps.length - 1 && (
                                  <div className={`w-0.5 h-6 ${isActive ? "bg-[rgb(var(--color-accent))]" : "bg-[rgb(var(--color-border))]"}`} />
                                )}
                              </div>
                              <div className="pb-5">
                                <p className={`font-semibold text-xs ${isActive || isCurrent ? "text-[rgb(var(--color-text))]" : "text-[rgb(var(--color-text-secondary))]"}`}>
                                  {shipmentLabels[step] || step}
                                </p>
                                {event && (
                                  <p className="text-[10px] text-[rgb(var(--color-text-secondary))] mt-0.5">
                                    {formatDateShort(event.occurred_at)}
                                    {event.note && ` — ${event.note}`}
                                  </p>
                                )}
                              </div>
                            </div>
                          );
                        })}
                      </div>
                    </div>
                  )}
                </>
              )}
            </div>
          </Card>

          {/* Detail info card */}
          <Card>
            <CardTitle>{t("details")}</CardTitle>
            <div className="mt-4 space-y-4 text-sm">
              <div className="flex justify-between">
                <span className="text-[rgb(var(--color-text-secondary))]">{t("created")}</span>
                <span className="font-semibold">{formatDateShort(order.created_at)}</span>
              </div>
              {order.updated_at && (
                <div className="flex justify-between">
                  <span className="text-[rgb(var(--color-text-secondary))]">{t("updated")}</span>
                  <span className="font-semibold">{formatDateShort(order.updated_at)}</span>
                </div>
              )}
              <div className="flex justify-between">
                <span className="text-[rgb(var(--color-text-secondary))]">العميل</span>
                <span className="font-semibold">#عميل-{order.user_id.slice(0, 6)}</span>
              </div>
            </div>
          </Card>
        </div>
      </div>
    </div>
  );
}
