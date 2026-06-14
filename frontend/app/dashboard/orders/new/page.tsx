"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { api } from "@/lib/api-client";
import { Card, CardTitle, Button, Input, Select, useToast, PageHeader } from "@/components/ui";
import { useTranslations } from "next-intl";

interface Product {
  id: string;
  name: string;
  price: number;
  stock: number;
  sku: string | null;
  is_active: boolean;
}

interface OrderItem {
  product_id: string;
  quantity: number;
}

export default function NewOrderPage() {
  const t = useTranslations("orders");
  const router = useRouter();
  const queryClient = useQueryClient();
  const { toast } = useToast();
  const token = typeof window !== "undefined" ? localStorage.getItem("access_token") : null;

  const { data: products, isLoading } = useQuery<Product[]>({
    queryKey: ["products"],
    queryFn: () => api.get("/products"),
    enabled: !!token,
  });

  const [items, setItems] = useState<OrderItem[]>([]);
  const [search, setSearch] = useState("");
  const [shippingProviderId, setShippingProviderId] = useState("");

  const { data: providers } = useQuery<any[]>({
    queryKey: ["shipping-providers"],
    queryFn: () => api.get("/shipping/providers"),
    enabled: !!token,
  });

  function toggleProduct(productId: string) {
    setItems((prev) => {
      const exists = prev.find((i) => i.product_id === productId);
      if (exists) return prev.filter((i) => i.product_id !== productId);
      return [...prev, { product_id: productId, quantity: 1 }];
    });
  }

  function updateQuantity(productId: string, quantity: number) {
    setItems((prev) =>
      prev.map((i) => (i.product_id === productId ? { ...i, quantity: Math.max(1, quantity) } : i))
    );
  }

  const activeProducts = (products?.filter((p) => p.is_active) ?? []).filter(
    (p) => !search || p.name.toLowerCase().includes(search.toLowerCase())
  );

  const mutation = useMutation({
    mutationFn: () => api.post("/orders", { items, shipping_provider_id: shippingProviderId || undefined }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["orders"] });
      toast(t("order_created"), "success");
      setTimeout(() => router.push("/dashboard/orders"), 1500);
    },
    onError: (err: Error) => toast(err.message, "error"),
  });

  const total = items.reduce((sum, item) => {
    const product = activeProducts.find((p) => p.id === item.product_id);
    return sum + (product ? product.price * item.quantity : 0);
  }, 0);

  return (
    <div className="space-y-6 animate-fade-in">
      <PageHeader title={t("title")} description={t("subtitle")} />

      <div className="grid lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2">
          <Card>
            <div className="flex items-center justify-between mb-4">
              <CardTitle>{t("select_products")}</CardTitle>
              <div className="relative w-48">
                <svg className="absolute right-3 top-1/2 -translate-y-1/2 w-4 h-4 text-[rgb(var(--color-text-secondary))] pointer-events-none" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                  <path strokeLinecap="round" strokeLinejoin="round" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
                </svg>
                <input
                  type="text"
                  value={search}
                  onChange={(e) => setSearch(e.target.value)}
                  placeholder="ابحث عن منتج..."
                  className="w-full pr-9 pl-3 py-1.5 bg-[rgb(var(--color-surface))] border border-[rgb(var(--color-border))] rounded-lg text-xs font-body focus:outline-none focus:border-[rgb(var(--color-accent))]"
                />
              </div>
            </div>
            <div className="space-y-2 max-h-[500px] overflow-y-auto">
              {isLoading && (
                <div className="space-y-3">
                  {[1, 2, 3].map((i) => (
                    <div key={i} className="h-16 bg-[rgb(var(--color-border))] rounded-lg animate-pulse" />
                  ))}
                </div>
              )}
              {activeProducts.map((product) => {
                const selected = items.find((i) => i.product_id === product.id);
                return (
                  <div
                    key={product.id}
                    className={`flex items-center justify-between p-3 rounded-lg border cursor-pointer transition-all ${
                      selected
                        ? "border-[rgb(var(--color-accent))] bg-[rgb(var(--color-accent-soft))]/30"
                        : "border-[rgb(var(--color-border))] hover:border-[rgb(var(--color-accent))] hover:shadow-sm"
                    }`}
                    onClick={() => toggleProduct(product.id)}
                  >
                    <div className="flex-1">
                      <p className="font-semibold text-sm">{product.name}</p>
                      <p className="text-xs text-[rgb(var(--color-text-secondary))]">{product.price.toLocaleString()} د.ج</p>
                    </div>
                    {selected ? (
                      <div className="flex items-center gap-2" onClick={(e) => e.stopPropagation()}>
                        <div className="flex items-center gap-1 bg-[rgb(var(--color-surface))] border border-[rgb(var(--color-border))] rounded-lg overflow-hidden">
                          <button
                            onClick={(e) => { e.stopPropagation(); updateQuantity(product.id, selected.quantity - 1); }}
                            className="px-2 py-1 text-sm hover:bg-[rgb(var(--color-accent-soft))] transition-colors"
                            disabled={selected.quantity <= 1}
                          >
                            −
                          </button>
                          <span className="px-2 py-1 text-sm font-semibold min-w-[24px] text-center">{selected.quantity}</span>
                          <button
                            onClick={(e) => { e.stopPropagation(); updateQuantity(product.id, selected.quantity + 1); }}
                            className="px-2 py-1 text-sm hover:bg-[rgb(var(--color-accent-soft))] transition-colors"
                          >
                            +
                          </button>
                        </div>
                        <span className="text-xs text-[rgb(var(--color-accent))] font-semibold">✓</span>
                      </div>
                    ) : (
                      <span className="text-lg text-[rgb(var(--color-text-secondary))] hover:text-[rgb(var(--color-accent))] transition-colors">+</span>
                    )}
                  </div>
                );
              })}
              {!isLoading && activeProducts.length === 0 && (
                <p className="text-sm text-[rgb(var(--color-text-secondary))] py-8 text-center">{t("no_products")}</p>
              )}
            </div>
          </Card>
        </div>

        <div>
          <Card className="sticky top-24">
            <CardTitle>{t("order_summary")}</CardTitle>
            <div className="mt-4 space-y-3">
              {items.length === 0 ? (
                <p className="text-sm text-[rgb(var(--color-text-secondary))]">{t("no_items")}</p>
              ) : (
                <div className="space-y-3">
                  {items.map((item) => {
                    const product = activeProducts.find((p) => p.id === item.product_id);
                    return (
                      <div key={item.product_id} className="flex justify-between items-center text-sm">
                        <div className="flex-1 min-w-0">
                          <p className="font-semibold truncate">{product?.name ?? "Unknown"}</p>
                        </div>
                        <div className="text-left shrink-0 mr-3">
                          <p className="font-semibold">{item.quantity} × {product?.price.toLocaleString()} د.ج</p>
                        </div>
                      </div>
                    );
                  })}
                  <div className="flex justify-between items-center pt-3 border-t border-[rgb(var(--color-border))]">
                    <span className="font-display text-sm font-bold">{t("total")}</span>
                    <span className="font-display text-xl font-extrabold text-[rgb(var(--color-accent))]">{total.toLocaleString()} د.ج</span>
                  </div>
                </div>
              )}

              <Select
                value={shippingProviderId}
                onChange={(e) => setShippingProviderId(e.target.value)}
                options={[
                  { value: "", label: t("no_provider") },
                  ...(providers ?? []).map((p: any) => ({ value: p.id, label: p.name })),
                ]}
                className="w-full"
              />

              <div className="flex gap-3 pt-3">
                <Button
                  onClick={() => mutation.mutate()}
                  disabled={items.length === 0 || mutation.isPending}
                  loading={mutation.isPending}
                  className="flex-1"
                >
                  {mutation.isPending ? t("creating") : t("create_order")}
                </Button>
                <Button variant="secondary" onClick={() => router.back()}>
                  {t("back")}
                </Button>
              </div>
            </div>
          </Card>
        </div>
      </div>
    </div>
  );
}
