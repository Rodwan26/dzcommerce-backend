"use client";
export const dynamic = "force-dynamic";

import { cn } from "@/lib/utils";
import { Card, CardTitle, Badge, PageSkeleton, KpiCard } from "@/components/ui";
import { useQuery } from "@tanstack/react-query";
import { useRouter } from "next/navigation";
import { api } from "@/lib/api-client";
import { formatDateShort, formatCurrency } from "@/lib/utils";
import { useTranslations } from "next-intl";

interface Stats {
  products_count?: number;
  orders_count?: number;
  revenue?: number;
  pending_orders?: number;
}

interface Order {
  id: string;
  status: string;
  total: number;
  created_at: string;
  items: { quantity: number }[];
}

export default function DashboardPage() {
  const t = useTranslations("dashboard_page");
  const to = useTranslations("orders");
  const router = useRouter();
  const token = typeof window !== "undefined" ? localStorage.getItem("access_token") : null;

  const { data: stats, isLoading: statsLoading } = useQuery<Stats>({
    queryKey: ["dashboard-stats"],
    queryFn: (): Promise<Stats> =>
      api.get<Stats>("/dashboard/stats").catch(() => ({
        products_count: 0,
        orders_count: 0,
        revenue: 0,
        pending_orders: 0,
      })),
    enabled: !!token,
  });

  const { data: recentOrders, isLoading: ordersLoading } = useQuery<Order[]>({
    queryKey: ["orders-recent"],
    queryFn: () => api.get("/orders"),
    enabled: !!token,
  });

  const statusBadge: Record<string, { label: string; variant: "warning" | "info" | "success" | "danger" }> = {
    pending: { label: to("status_pending"), variant: "warning" },
    confirmed: { label: to("status_confirmed"), variant: "info" },
    shipped: { label: to("status_shipped"), variant: "info" },
    delivered: { label: to("status_delivered"), variant: "success" },
    returned: { label: to("status_returned"), variant: "danger" },
    cancelled: { label: to("status_cancelled"), variant: "danger" },
  };

  const latestOrders = (recentOrders ?? []).slice(0, 5);

  if (statsLoading && ordersLoading) return <PageSkeleton />;

  return (
    <div className="space-y-8 animate-fade-in">
      {/* Header */}
      <div>
        <h1 className="font-display text-2xl sm:text-3xl font-extrabold tracking-tight">{t("title")}</h1>
        <p className="text-[rgb(var(--color-text-secondary))] mt-1 text-sm">{t("welcome")}</p>
      </div>

      {/* KPI Cards */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <KpiCard
          icon="📦"
          value={String(stats?.products_count ?? 0)}
          label={t("stat_products")}
          color="navy"
          isLoading={statsLoading}
          trend={{ value: "12%", positive: true }}
        />
        <KpiCard
          icon="📋"
          value={String(stats?.orders_count ?? 0)}
          label={t("stat_orders")}
          color="terra"
          isLoading={statsLoading}
          trend={{ value: "8%", positive: true }}
        />
        <KpiCard
          icon="💰"
          value={stats?.revenue ? `${stats.revenue.toLocaleString()} د.ج` : "0 د.ج"}
          label={t("stat_revenue")}
          color="emerald"
          isLoading={statsLoading}
          trend={{ value: "23%", positive: true }}
        />
        <KpiCard
          icon="⏳"
          value={String(stats?.pending_orders ?? 0)}
          label={t("stat_pending")}
          color="amber"
          isLoading={statsLoading}
          trend={{ value: "3%", positive: false }}
        />
      </div>

      {/* Quick Actions */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
        {[
          { label: t("action_add_product"), href: "/dashboard/products", icon: "➕" },
          { label: t("action_new_order"), href: "/dashboard/orders/new", icon: "🛒" },
          { label: t("action_sales_report"), href: "/dashboard/orders", icon: "📊" },
          { label: t("action_settings"), href: "/dashboard/settings", icon: "⚙️" },
        ].map((action) => (
          <button
            key={action.label}
            onClick={() => router.push(action.href)}
            className="flex flex-col items-center gap-2 p-4 rounded-xl bg-[rgb(var(--color-surface))] border border-[rgb(var(--color-border))] hover:border-[rgb(var(--color-accent))] hover:shadow-md hover:-translate-y-0.5 transition-all duration-150"
          >
            <span className="text-2xl">{action.icon}</span>
            <span className="font-display text-xs font-semibold text-[rgb(var(--color-text-secondary))]">
              {action.label}
            </span>
          </button>
        ))}
      </div>

      {/* Revenue Chart Placeholder */}
      <Card>
        <div className="flex items-center justify-between mb-4">
          <CardTitle>الإيرادات</CardTitle>
          <div className="flex gap-1">
            {["أسبوعي", "شهري", "سنوي"].map((label) => (
              <button key={label} className={cn(
                "px-3 py-1 text-xs font-display font-semibold rounded-lg transition-colors",
                label === "شهري"
                  ? "bg-[rgb(var(--color-accent))] text-white"
                  : "text-[rgb(var(--color-text-secondary))] hover:bg-[rgb(var(--color-accent-soft))]"
              )}>
                {label}
              </button>
            ))}
          </div>
        </div>
        <div className="h-64 rounded-lg bg-gradient-to-b from-[rgb(var(--color-accent-soft))]/50 to-transparent flex items-center justify-center">
          <div className="text-center">
            <span className="text-3xl block mb-2">📈</span>
            <p className="text-sm text-[rgb(var(--color-text-secondary))] font-display font-semibold">مخطط الإيرادات</p>
          </div>
        </div>
      </Card>

      {/* Recent Orders + Activity */}
      <div className="grid lg:grid-cols-2 gap-6">
        <Card>
          <div className="flex items-center justify-between mb-4">
            <CardTitle>آخر الطلبات</CardTitle>
            <button
              onClick={() => router.push("/dashboard/orders")}
              className="text-xs font-display font-semibold text-[rgb(var(--color-accent))] hover:underline"
            >
              عرض الكل
            </button>
          </div>
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-[rgb(var(--color-border))]">
                  <th className="text-right py-3 px-3 font-display font-semibold text-xs text-[rgb(var(--color-text-secondary))]">#</th>
                  <th className="text-right py-3 px-3 font-display font-semibold text-xs text-[rgb(var(--color-text-secondary))]">{to("table_items")}</th>
                  <th className="text-right py-3 px-3 font-display font-semibold text-xs text-[rgb(var(--color-text-secondary))]">{to("table_total")}</th>
                  <th className="text-right py-3 px-3 font-display font-semibold text-xs text-[rgb(var(--color-text-secondary))]">{to("table_status")}</th>
                  <th className="text-right py-3 px-3 font-display font-semibold text-xs text-[rgb(var(--color-text-secondary))]">{to("table_date")}</th>
                </tr>
              </thead>
              <tbody>
                {latestOrders.length === 0 ? (
                  <tr>
                    <td colSpan={5} className="text-center py-10 text-[rgb(var(--color-text-secondary))] text-sm">{to("empty")}</td>
                  </tr>
                ) : (
                  latestOrders.map((order) => {
                    const st = statusBadge[order.status] || statusBadge.pending;
                    return (
                      <tr
                        key={order.id}
                        onClick={() => router.push(`/dashboard/orders/${order.id}`)}
                        className="border-b border-[rgb(var(--color-border))] last:border-0 hover:bg-[rgb(var(--color-accent-soft))]/30 transition-colors cursor-pointer"
                      >
                        <td className="py-3 px-3 font-display font-semibold">#{order.id.slice(0, 8)}</td>
                        <td className="py-3 px-3 text-[rgb(var(--color-text-secondary))]">{order.items?.length ?? 0}</td>
                        <td className="py-3 px-3 font-semibold">{formatCurrency(order.total)}</td>
                        <td className="py-3 px-3"><Badge variant={st.variant}>{st.label}</Badge></td>
                        <td className="py-3 px-3 text-[rgb(var(--color-text-secondary))] text-xs">{formatDateShort(order.created_at)}</td>
                      </tr>
                    );
                  })
                )}
              </tbody>
            </table>
          </div>
        </Card>

        <Card>
          <CardTitle>النشاط الأخير</CardTitle>
          <div className="mt-4 space-y-4">
            {[
              { icon: "📦", text: "تم إضافة منتج جديد", time: "منذ 5 دقائق" },
              { icon: "📋", text: "طلب جديد #abc123", time: "منذ 15 دقيقة" },
              { icon: "🚚", text: "تم شحن الطلب #abc120", time: "منذ ساعة" },
              { icon: "💰", text: "تم تأكيد الطلب #abc119", time: "منذ ساعتين" },
              { icon: "⚙️", text: "تم تحديث الإعدادات", time: "منذ 3 ساعات" },
            ].map((activity, i) => (
              <div key={i} className="flex items-start gap-3">
                <div className="w-8 h-8 rounded-lg bg-[rgb(var(--color-accent-soft))] flex items-center justify-center shrink-0">
                  <span className="text-sm">{activity.icon}</span>
                </div>
                <div className="flex-1 min-w-0">
                  <p className="text-sm font-display font-semibold truncate">{activity.text}</p>
                  <p className="text-xs text-[rgb(var(--color-text-secondary))]">{activity.time}</p>
                </div>
              </div>
            ))}
          </div>
        </Card>
      </div>
    </div>
  );
}
