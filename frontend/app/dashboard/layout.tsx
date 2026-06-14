"use client";

import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { cn } from "@/lib/utils";
import { clearTokens } from "@/lib/api-client";
import { useEffect, useState } from "react";
import { useTranslations } from "next-intl";
import { isAuthenticated } from "@/lib/auth";
import LanguageSwitcher from "@/components/layout/LanguageSwitcher";
import { Avatar } from "@/components/ui";

export default function DashboardLayout({ children }: { children: React.ReactNode }) {
  const t = useTranslations("dashboard");
  const pathname = usePathname();
  const router = useRouter();
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false);
  const [authChecked, setAuthChecked] = useState(false);
  const [darkMode, setDarkMode] = useState(false);
  const [userMenuOpen, setUserMenuOpen] = useState(false);

  useEffect(() => {
    const auth = isAuthenticated();
    if (!auth) {
      router.replace("/login");
      return;
    }
    setAuthChecked(true);
  }, []);

  useEffect(() => {
    if (darkMode) {
      document.documentElement.classList.add("dark");
    } else {
      document.documentElement.classList.remove("dark");
    }
  }, [darkMode]);

  useEffect(() => {
    setSidebarOpen(false);
    setUserMenuOpen(false);
  }, [pathname]);

  useEffect(() => {
    const handler = (e: MouseEvent) => setUserMenuOpen(false);
    document.addEventListener("mousedown", handler);
    return () => document.removeEventListener("mousedown", handler);
  }, []);

  if (!authChecked) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-[rgb(var(--color-bg))]">
        <div className="flex flex-col items-center gap-3">
          <svg className="animate-spin h-8 w-8 text-[rgb(var(--color-accent))]" fill="none" viewBox="0 0 24 24">
            <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
            <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
          </svg>
        </div>
      </div>
    );
  }

  const navItems = [
    { href: "/dashboard", label: t("nav_home"), icon: "📊" },
    { href: "/dashboard/products", label: t("nav_products"), icon: "📦" },
    { href: "/dashboard/orders", label: t("nav_orders"), icon: "📋" },
    { href: "/dashboard/marketing", label: t("nav_marketing"), icon: "📈" },
    { href: "/dashboard/shipping", label: t("nav_shipping"), icon: "🚚" },
    { href: "/dashboard/settings", label: t("nav_settings"), icon: "⚙️" },
  ];

  function handleLogout() {
    clearTokens();
    router.push("/login");
  }

  return (
    <div className="min-h-screen bg-[rgb(var(--color-bg))]">
      {/* Mobile header */}
      <div className="lg:hidden fixed top-0 left-0 right-0 z-40 h-14 bg-[rgb(var(--color-surface))]/80 backdrop-blur-lg border-b border-[rgb(var(--color-border))] flex items-center justify-between px-4">
        <button onClick={() => setSidebarOpen(!sidebarOpen)} className="p-1.5 rounded-lg hover:bg-[rgb(var(--color-accent-soft))] transition-colors">
          {sidebarOpen ? (
            <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M6 18L18 6M6 6l12 12" />
            </svg>
          ) : (
            <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M4 6h16M4 12h16M4 18h16" />
            </svg>
          )}
        </button>
        <Link href="/dashboard" className="font-display text-lg font-extrabold tracking-tight">
          Dz<span className="text-[rgb(var(--color-accent))]">C</span>
        </Link>
        <LanguageSwitcher mini />
      </div>

      {/* Sidebar overlay */}
      {sidebarOpen && (
        <div
          className="lg:hidden fixed inset-0 z-30 bg-black/40 backdrop-blur-sm"
          onClick={() => setSidebarOpen(false)}
        />
      )}

      {/* Sidebar */}
      <aside
        className={cn(
          "fixed top-0 bottom-0 z-40 flex flex-col bg-[rgb(var(--color-surface))]/90 backdrop-blur-xl border-l border-[rgb(var(--color-border))] transition-all duration-300",
          sidebarCollapsed ? "w-[68px]" : "w-64",
          "rtl:right-0 rtl:border-l rtl:border-r-0",
          sidebarOpen ? "translate-x-0" : "rtl:translate-x-full lg:rtl:translate-x-0"
        )}
      >
        {/* Logo + Toggle */}
        <div className="h-16 flex items-center justify-between px-4 border-b border-[rgb(var(--color-border))]">
          {sidebarCollapsed ? (
            <Link href="/dashboard" className="font-display text-xl font-extrabold tracking-tight mx-auto">
              Dz<span className="text-[rgb(var(--color-accent))]">C</span>
            </Link>
          ) : (
            <Link href="/dashboard" className="font-display text-xl font-extrabold tracking-tight">
              Dz<span className="text-[rgb(var(--color-accent))]">Commerce</span>
            </Link>
          )}
          <button
            onClick={() => setSidebarCollapsed(!sidebarCollapsed)}
            className="hidden lg:flex items-center justify-center w-7 h-7 rounded-lg text-[rgb(var(--color-text-secondary))] hover:text-[rgb(var(--color-text))] hover:bg-[rgb(var(--color-accent-soft))] transition-colors"
          >
            <svg className={cn("w-4 h-4 transition-transform", sidebarCollapsed && "rotate-180")} fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M15 19l-7-7 7-7" />
            </svg>
          </button>
        </div>

        {/* Nav */}
        <nav className="flex-1 p-3 space-y-1 overflow-y-auto">
          {navItems.map((item) => {
            const isActive = pathname === item.href ||
              (item.href !== "/dashboard" && pathname.startsWith(item.href));
            return (
              <Link
                key={item.href}
                href={item.href}
                className={cn(
                  "flex items-center gap-3 px-3 py-2.5 rounded-lg font-display font-semibold text-sm transition-all duration-150 group",
                  isActive
                    ? "bg-[rgb(var(--color-accent-soft))] text-[rgb(var(--color-accent))]"
                    : "text-[rgb(var(--color-text-secondary))] hover:text-[rgb(var(--color-text))] hover:bg-[rgb(var(--color-accent-soft))]/50"
                )}
                title={sidebarCollapsed ? item.label : undefined}
              >
                <span className="text-lg shrink-0">{item.icon}</span>
                {!sidebarCollapsed && (
                  <span className="truncate">{item.label}</span>
                )}
                {isActive && !sidebarCollapsed && (
                  <span className="w-1 h-4 rounded-full bg-[rgb(var(--color-accent))] mr-auto" />
                )}
              </Link>
            );
          })}
        </nav>

        {/* Logout */}
        <div className="p-3 border-t border-[rgb(var(--color-border))]">
          {sidebarCollapsed ? (
            <button
              onClick={handleLogout}
              className="flex items-center justify-center w-full p-2.5 rounded-lg text-[rgb(var(--color-text-secondary))] hover:text-[rgb(var(--color-danger))] hover:bg-red-50 transition-all duration-150"
              title="Logout"
            >
              <span className="text-lg">🚪</span>
            </button>
          ) : (
            <button
              onClick={handleLogout}
              className="flex items-center gap-3 px-3 py-2.5 w-full rounded-lg font-display font-semibold text-sm text-[rgb(var(--color-text-secondary))] hover:text-[rgb(var(--color-danger))] hover:bg-red-50 transition-all duration-150"
            >
              <span className="text-lg">🚪</span>
              {t("logout")}
            </button>
          )}
        </div>
      </aside>

      {/* Main content area */}
      <div className={cn("transition-all duration-300", sidebarCollapsed ? "lg:mr-[68px]" : "lg:mr-64")}>
        {/* Top Header */}
        <header className="sticky top-0 z-20 h-16 bg-[rgb(var(--color-surface))]/70 backdrop-blur-xl border-b border-[rgb(var(--color-border))]">
          <div className="flex items-center justify-between h-full px-6">
            {/* Right side: empty for spacing in RTL */}
            <div />

            {/* Left side: actions */}
            <div className="flex items-center gap-2">
              {/* Dark mode toggle */}
              <button
                onClick={() => setDarkMode(!darkMode)}
                className="p-2 rounded-lg text-[rgb(var(--color-text-secondary))] hover:text-[rgb(var(--color-text))] hover:bg-[rgb(var(--color-accent-soft))] transition-all"
                title={darkMode ? "Light mode" : "Dark mode"}
              >
                {darkMode ? (
                  <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                    <path strokeLinecap="round" strokeLinejoin="round" d="M12 3v1m0 16v1m9-9h-1M4 12H3m15.364 6.364l-.707-.707M6.343 6.343l-.707-.707m12.728 0l-.707.707M6.343 17.657l-.707.707M16 12a4 4 0 11-8 0 4 4 0 018 0z" />
                  </svg>
                ) : (
                  <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                    <path strokeLinecap="round" strokeLinejoin="round" d="M20.354 15.354A9 9 0 018.646 3.646 9.003 9.003 0 0012 21a9.003 9.003 0 008.354-5.646z" />
                  </svg>
                )}
              </button>

              {/* Language switcher */}
              <LanguageSwitcher mini />

              {/* Notification bell */}
              <button className="p-2 rounded-lg text-[rgb(var(--color-text-secondary))] hover:text-[rgb(var(--color-text))] hover:bg-[rgb(var(--color-accent-soft))] transition-all relative">
                <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                  <path strokeLinecap="round" strokeLinejoin="round" d="M15 17h5l-1.405-1.405A2.032 2.032 0 0118 14.158V11a6.002 6.002 0 00-4-5.659V5a2 2 0 10-4 0v.341C7.67 6.165 6 8.388 6 11v3.159c0 .538-.214 1.055-.595 1.436L4 17h5m6 0v1a3 3 0 11-6 0v-1m6 0H9" />
                </svg>
                <span className="absolute top-1.5 right-1.5 w-2 h-2 rounded-full bg-[rgb(var(--color-danger))]" />
              </button>

              {/* User Avatar */}
              <div className="relative">
                <button
                  onClick={(e) => { e.stopPropagation(); setUserMenuOpen(!userMenuOpen); }}
                  className="p-1 rounded-lg hover:bg-[rgb(var(--color-accent-soft))] transition-colors"
                >
                  <Avatar name="Admin User" size="sm" />
                </button>
                {userMenuOpen && (
                  <div className="absolute top-full mt-2 left-0 z-50 min-w-[180px] bg-[rgb(var(--color-surface))] border border-[rgb(var(--color-border))] rounded-xl shadow-2xl py-1 animate-scale-in"
                    onClick={(e) => e.stopPropagation()}
                  >
                    <div className="px-4 py-3 border-b border-[rgb(var(--color-border))]">
                      <p className="font-display font-semibold text-sm">Admin User</p>
                      <p className="text-xs text-[rgb(var(--color-text-secondary))]">admin@dz.com</p>
                    </div>
                    <button
                      onClick={handleLogout}
                      className="flex items-center gap-2 w-full px-4 py-2.5 text-sm font-display font-semibold text-[rgb(var(--color-danger))] hover:bg-red-50 transition-colors"
                    >
                      <span>🚪</span>
                      {t("logout")}
                    </button>
                  </div>
                )}
              </div>
            </div>
          </div>
        </header>

        {/* Page content */}
        <main className="p-6 max-w-6xl mx-auto">
          {children}
        </main>
      </div>
    </div>
  );
}
