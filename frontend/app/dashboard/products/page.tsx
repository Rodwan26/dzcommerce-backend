"use client";
export const dynamic = "force-dynamic";

import { useState, useMemo } from "react";
import { Button, Badge, SearchBar, PageHeader, TableSkeleton } from "@/components/ui";
import { Table, type Column } from "@/components/ui/Table";
import { ProductFormModal } from "@/components/forms/ProductFormModal";
import { useQuery } from "@tanstack/react-query";
import { api } from "@/lib/api-client";
import { useTranslations } from "next-intl";

interface Product {
  id: string;
  name: string;
  price: number;
  stock: number;
  sku: string | null;
  is_active: boolean;
}

export default function ProductsPage() {
  const t = useTranslations("products");
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [selectedProduct, setSelectedProduct] = useState<Product | null>(null);
  const [search, setSearch] = useState("");
  const [statusFilter, setStatusFilter] = useState<"all" | "active" | "inactive">("all");

  const token = typeof window !== "undefined" ? localStorage.getItem("access_token") : null;
  const { data: products, isLoading } = useQuery<Product[]>({
    queryKey: ["products"],
    queryFn: () => api.get("/products"),
    enabled: !!token,
  });

  const filtered = useMemo(() => {
    if (!products) return [];
    return products.filter((p) => {
      const matchesSearch = !search || p.name.toLowerCase().includes(search.toLowerCase()) || (p.sku?.toLowerCase().includes(search.toLowerCase()));
      const matchesStatus = statusFilter === "all" || (statusFilter === "active" && p.is_active) || (statusFilter === "inactive" && !p.is_active);
      return matchesSearch && matchesStatus;
    });
  }, [products, search, statusFilter]);

  const columns: Column<Product>[] = [
    { key: "name", label: t("table_name"), sortable: true, className: "font-semibold" },
    {
      key: "price",
      label: t("table_price"),
      sortable: true,
      render: (p) => <span dir="ltr">{p.price.toLocaleString()} د.ج</span>,
    },
    { key: "stock", label: t("table_stock"), sortable: true },
    {
      key: "is_active",
      label: t("table_status"),
      render: (p) =>
        p.is_active ? (
          <Badge variant="success">{t("status_active")}</Badge>
        ) : (
          <Badge variant="danger">{t("status_inactive")}</Badge>
        ),
    },
    {
      key: "actions",
      label: "",
      render: (p) => (
        <Button variant="ghost" size="sm" onClick={(e) => { e.stopPropagation(); openEditModal(p); }}>
          {t("edit")}
        </Button>
      ),
    },
  ];

  function openCreateModal() {
    setSelectedProduct(null);
    setIsModalOpen(true);
  }

  function openEditModal(product: Product) {
    setSelectedProduct(product);
    setIsModalOpen(true);
  }

  function closeModal() {
    setIsModalOpen(false);
    setSelectedProduct(null);
  }

  return (
    <div className="space-y-6 animate-fade-in">
      <ProductFormModal isOpen={isModalOpen} onClose={closeModal} product={selectedProduct} />

      <PageHeader
        title={t("title")}
        description={t("subtitle")}
        actions={<Button onClick={openCreateModal}>{t("add_product")}</Button>}
      />

      {/* Filters */}
      <div className="flex flex-col sm:flex-row gap-3 items-start sm:items-center justify-between">
        <div className="flex gap-1">
          {(["all", "active", "inactive"] as const).map((filter) => (
            <button
              key={filter}
              onClick={() => setStatusFilter(filter)}
              className={`px-3 py-1.5 text-xs font-display font-semibold rounded-lg transition-colors ${
                statusFilter === filter
                  ? "bg-[rgb(var(--color-accent))] text-white"
                  : "text-[rgb(var(--color-text-secondary))] hover:bg-[rgb(var(--color-accent-soft))]"
              }`}
            >
              {filter === "all" ? "الكل" : filter === "active" ? t("status_active") : t("status_inactive")}
            </button>
          ))}
        </div>
        <SearchBar value={search} onChange={setSearch} placeholder={t("table_name") + "..."} className="w-full sm:w-64" />
      </div>

      {isLoading ? (
        <TableSkeleton rows={5} cols={4} />
      ) : (
        <div className="bg-[rgb(var(--color-surface))] border border-[rgb(var(--color-border))] rounded-xl shadow-[0_1px_3px_rgba(0,0,0,0.04)]">
          <Table
            columns={columns}
            data={filtered}
            keyExtractor={(p) => p.id}
            emptyLabel={t("empty")}
            searchable={false}
            pageSize={10}
          />
        </div>
      )}
    </div>
  );
}
