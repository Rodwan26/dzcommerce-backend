"use client";

import { useEffect } from "react";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { api } from "@/lib/api-client";
import { Button, Input, Modal, useToast } from "@/components/ui";

const productSchema = z.object({
  name: z.string().min(1, "Name is required"),
  price: z.coerce.number().positive("Price must be positive"),
  stock: z.coerce.number().int().min(0, "Stock cannot be negative"),
  sku: z.string().optional(),
});

type ProductFormData = z.infer<typeof productSchema>;

interface Product {
  id: string;
  name: string;
  price: number;
  stock: number;
  sku: string | null;
  is_active: boolean;
}

interface ProductFormModalProps {
  isOpen: boolean;
  onClose: () => void;
  product?: Product | null;
}

export function ProductFormModal({ isOpen, onClose, product }: ProductFormModalProps) {
  const queryClient = useQueryClient();
  const { toast } = useToast();
  const isEdit = !!product;

  const {
    register,
    handleSubmit,
    reset,
    formState: { errors },
  } = useForm<ProductFormData>({
    resolver: zodResolver(productSchema),
  });

  useEffect(() => {
    if (product) {
      reset({
        name: product.name,
        price: product.price,
        stock: product.stock,
        sku: product.sku ?? "",
      });
    } else {
      reset({ name: "", price: 0, stock: 0, sku: "" });
    }
  }, [product, isOpen, reset]);

  const mutation = useMutation({
    mutationFn: async (data: ProductFormData) => {
      if (isEdit) {
        return api.put(`/products/${product!.id}`, data);
      }
      return api.post("/products", data);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["products"] });
      toast(isEdit ? "Product updated" : "Product created", "success");
      onClose();
    },
    onError: (err: Error) => {
      toast(err.message, "error");
    },
  });

  return (
    <Modal isOpen={isOpen} onClose={onClose} title={isEdit ? "Edit Product" : "Add Product"}>
      <form onSubmit={handleSubmit((data) => mutation.mutate(data))} className="space-y-4">
        <Input
          label="Name"
          id="name"
          error={errors.name?.message}
          {...register("name")}
        />

        <Input
          label="Price"
          id="price"
          type="number"
          step="0.01"
          min="0"
          error={errors.price?.message}
          {...register("price")}
        />

        <Input
          label="Stock"
          id="stock"
          type="number"
          min="0"
          error={errors.stock?.message}
          {...register("stock")}
        />

        <Input
          label="SKU"
          id="sku"
          error={errors.sku?.message}
          {...register("sku")}
        />

        <div className="flex items-center gap-3 pt-2">
          <Button type="submit" disabled={mutation.isPending}>
            {mutation.isPending ? "Saving..." : isEdit ? "Update" : "Create"}
          </Button>
          <Button type="button" variant="secondary" onClick={onClose}>
            Cancel
          </Button>
        </div>
      </form>
    </Modal>
  );
}
