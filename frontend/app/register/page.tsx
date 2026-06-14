"use client";

import Link from "next/link";
import { Button, Input } from "@/components/ui";
import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { useTranslations } from "next-intl";
import { isAuthenticated } from "@/lib/auth";
import LanguageSwitcher from "@/components/layout/LanguageSwitcher";

export default function RegisterPage() {
  const t = useTranslations("register");
  const router = useRouter();

  useEffect(() => {
    if (isAuthenticated()) {
      router.replace("/dashboard");
    }
  }, []);

  const [form, setForm] = useState({
    name: "",
    email: "",
    phone: "",
    company_name: "",
    password: "",
  });
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");
  const [loading, setLoading] = useState(false);
  const [showPassword, setShowPassword] = useState(false);

  function updateField(key: string, value: string) {
    setForm((prev) => ({ ...prev, [key]: value }));
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError("");
    setSuccess("");
    setLoading(true);
    try {
      const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
      const res = await fetch(`${API_BASE}/auth/register`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(form),
      });
      if (!res.ok) {
        const data = await res.json();
        throw new Error(data.detail || t("error_failed"));
      }
      setSuccess(t("success"));
    } catch (err: any) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-[rgb(var(--color-navy-900))] via-[rgb(var(--color-navy-800))] to-[rgb(var(--color-navy-700))] flex items-center justify-center p-4 relative overflow-hidden">
      {/* Ambient background effects */}
      <div className="absolute inset-0 overflow-hidden">
        <div className="absolute -top-40 -left-40 w-96 h-96 rounded-full bg-[rgb(var(--color-accent))]/5 blur-3xl animate-pulse-soft" />
        <div className="absolute -bottom-40 -right-40 w-80 h-80 rounded-full bg-white/[0.02] blur-3xl" />
      </div>

      <div className="relative z-10 w-full max-w-sm">
        {/* Logo */}
        <div className="text-center mb-8">
          <Link href="/" className="font-display text-2xl font-extrabold tracking-tight text-white">
            Dz<span className="text-[rgb(var(--color-accent))]">Commerce</span>
          </Link>
        </div>

        {/* Card */}
        <div className="backdrop-blur-xl bg-white/10 rounded-2xl p-8 border border-white/10 shadow-2xl animate-fade-up">
          <div className="flex items-center justify-between mb-6">
            <div>
              <h1 className="font-display text-2xl font-extrabold text-white mb-1">{t("title")}</h1>
              <p className="text-sm text-white/60">{t("subtitle")}</p>
            </div>
            <LanguageSwitcher mini />
          </div>

          <form onSubmit={handleSubmit} className="space-y-4">
            {error && (
              <div className="p-3 rounded-lg bg-red-500/20 border border-red-500/30 text-sm text-red-200 font-medium animate-slide-down">
                {error}
              </div>
            )}
            {success && (
              <div className="p-3 rounded-lg bg-emerald-500/20 border border-emerald-500/30 text-sm text-emerald-200 font-medium animate-slide-down">
                {success}
              </div>
            )}

            <Input
              label={t("name_label")}
              id="name"
              placeholder={t("name_placeholder")}
              value={form.name}
              onChange={(e) => updateField("name", e.target.value)}
              required
              className="!bg-white/10 !border-white/20 !text-white placeholder:!text-white/40"
            />

            <Input
              label={t("company_label")}
              id="company_name"
              placeholder={t("company_placeholder")}
              value={form.company_name}
              onChange={(e) => updateField("company_name", e.target.value)}
              required
              className="!bg-white/10 !border-white/20 !text-white placeholder:!text-white/40"
            />

            <Input
              label={t("email_label")}
              id="email"
              type="email"
              placeholder={t("email_placeholder")}
              value={form.email}
              onChange={(e) => updateField("email", e.target.value)}
              required
              className="!bg-white/10 !border-white/20 !text-white placeholder:!text-white/40"
            />

            <Input
              label={t("phone_label")}
              id="phone"
              type="tel"
              placeholder={t("phone_placeholder")}
              value={form.phone}
              onChange={(e) => updateField("phone", e.target.value)}
              required
              className="!bg-white/10 !border-white/20 !text-white placeholder:!text-white/40"
            />

            <Input
              label={t("password_label")}
              id="password"
              type={showPassword ? "text" : "password"}
              placeholder={t("password_placeholder")}
              value={form.password}
              onChange={(e) => updateField("password", e.target.value)}
              required
              className="!bg-white/10 !border-white/20 !text-white placeholder:!text-white/40"
              rightIcon={
                <button
                  type="button"
                  onClick={() => setShowPassword(!showPassword)}
                  className="text-white/40 hover:text-white/70 transition-colors"
                >
                  {showPassword ? (
                    <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                      <path strokeLinecap="round" strokeLinejoin="round" d="M13.875 18.825A10.05 10.05 0 0112 19c-4.478 0-8.268-2.943-9.543-7a9.97 9.97 0 011.563-3.029m5.858.908a3 3 0 114.243 4.243M9.878 9.878l4.242 4.242M9.88 9.88l-3.29-3.29m7.532 7.532l3.29 3.29M3 3l3.59 3.59m0 0A9.953 9.953 0 0112 5c4.478 0 8.268 2.943 9.543 7a10.025 10.025 0 01-4.132 5.411m0 0L21 21" />
                    </svg>
                  ) : (
                    <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                      <path strokeLinecap="round" strokeLinejoin="round" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                      <path strokeLinecap="round" strokeLinejoin="round" d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" />
                    </svg>
                  )}
                </button>
              }
            />

            <Button type="submit" className="w-full !bg-[rgb(var(--color-accent))] hover:!brightness-110" disabled={loading} loading={loading}>
              {loading ? t("submitting") : t("submit")}
            </Button>
          </form>

          <p className="mt-6 text-center text-sm text-white/50">
            {t("has_account")}{" "}
            <Link href="/login" className="text-[rgb(var(--color-accent))] font-semibold hover:underline">
              {t("has_account_link")}
            </Link>
          </p>
        </div>
      </div>
    </div>
  );
}
