import Link from "next/link";
import { getTranslations } from "next-intl/server";
import { Button } from "@/components/ui";
import LanguageSwitcher from "@/components/layout/LanguageSwitcher";

export default async function LandingPage() {
  const t = await getTranslations("landing");

  return (
    <div className="min-h-screen bg-[rgb(var(--color-bg))]">
      {/* Navigation */}
      <header className="fixed top-0 left-0 right-0 z-50 glass border-b border-[rgb(var(--color-border))]">
        <div className="max-w-7xl mx-auto px-6 h-16 flex items-center justify-between">
          <Link href="/" className="font-display text-xl font-extrabold tracking-tight">
            Dz<span className="text-[rgb(var(--color-accent))]">Commerce</span>
          </Link>
          <nav className="flex items-center gap-3">
            <LanguageSwitcher mini />
            <Link href="/login">
              <Button variant="ghost" size="sm">{t("nav_login")}</Button>
            </Link>
            <Link href="/register">
              <Button size="sm">{t("nav_register")}</Button>
            </Link>
          </nav>
        </div>
      </header>

      {/* Hero */}
      <section className="relative pt-36 pb-24 px-6 overflow-hidden">
        <div className="absolute inset-0 bg-gradient-to-b from-[rgb(var(--color-accent-soft))]/60 to-transparent" />
        <div className="absolute top-1/4 -left-32 w-96 h-96 rounded-full bg-[rgb(var(--color-accent))]/5 blur-3xl" />
        <div className="absolute top-1/3 -right-32 w-80 h-80 rounded-full bg-[rgb(var(--color-navy-500))]/5 blur-3xl" />
        <div className="max-w-5xl mx-auto text-center relative">
          <div className="animate-fade-up">
            <span className="inline-flex items-center gap-1.5 px-4 py-1.5 mb-6 text-xs font-semibold font-display tracking-wider uppercase bg-[rgb(var(--color-accent-soft))] text-[rgb(var(--color-accent))] rounded-full">
              <span className="w-1.5 h-1.5 rounded-full bg-[rgb(var(--color-accent))] animate-pulse-soft" />
              {t("brand_tagline")}
            </span>
            <h1 className="font-display text-5xl md:text-7xl font-extrabold tracking-tight leading-[1.1] mb-6">
              {t("hero_title")}
              <br />
              <span className="text-[rgb(var(--color-accent))]">{t("hero_title_highlight")}</span>
            </h1>
            <p className="text-lg md:text-xl text-[rgb(var(--color-text-secondary))] max-w-2xl mx-auto mb-10 leading-relaxed">
              {t("hero_desc")}
            </p>
            <div className="flex items-center justify-center gap-4">
              <Link href="/register">
                <Button size="lg">{t("hero_cta")}</Button>
              </Link>
              <Link href="/login">
                <Button variant="secondary" size="lg">{t("hero_login")}</Button>
              </Link>
            </div>
          </div>
        </div>
      </section>

      {/* Stats */}
      <section className="py-16 px-6 bg-[rgb(var(--color-surface))] border-y border-[rgb(var(--color-border))]">
        <div className="max-w-6xl mx-auto grid grid-cols-2 md:grid-cols-4 gap-8">
          {[
            { value: "100+", label: "تاجر" },
            { value: "5,000+", label: "طلب" },
            { value: "50M+", label: "دينار معاملات" },
            { value: "99.9%", label: "وقت تشغيل" },
          ].map((stat) => (
            <div key={stat.label} className="text-center">
              <p className="font-display text-3xl md:text-4xl font-extrabold text-[rgb(var(--color-accent))]">{stat.value}</p>
              <p className="text-sm text-[rgb(var(--color-text-secondary))] mt-1">{stat.label}</p>
            </div>
          ))}
        </div>
      </section>

      {/* Features */}
      <section className="py-24 px-6">
        <div className="max-w-6xl mx-auto">
          <div className="text-center mb-16 animate-fade-up">
            <h2 className="font-display text-3xl md:text-4xl font-extrabold mb-4">
              {t("features_title")}
            </h2>
            <p className="text-[rgb(var(--color-text-secondary))] text-lg max-w-xl mx-auto">
              {t("features_desc")}
            </p>
          </div>

          <div className="grid md:grid-cols-3 gap-6">
            {[
              { title: t("feature_inventory"), desc: t("feature_inventory_desc"), icon: "📦", from: "#3a5f84", to: "#1f3a55" },
              { title: t("feature_orders"), desc: t("feature_orders_desc"), icon: "📋", from: "#b6612e", to: "#733b1b" },
              { title: t("feature_cod"), desc: t("feature_cod_desc"), icon: "💵", from: "#059669", to: "#065f46" },
              { title: t("feature_reports"), desc: t("feature_reports_desc"), icon: "📊", from: "#3a5f84", to: "#1f3a55" },
              { title: t("feature_whatsapp"), desc: t("feature_whatsapp_desc"), icon: "💬", from: "#059669", to: "#065f46" },
              { title: t("feature_excel"), desc: t("feature_excel_desc"), icon: "📄", from: "#b6612e", to: "#733b1b" },
            ].map((feature, i) => (
              <div
                key={feature.title}
                className="group relative overflow-hidden rounded-xl bg-[rgb(var(--color-surface))] border border-[rgb(var(--color-border))] p-6 hover:shadow-lg hover:-translate-y-1 transition-all duration-200 animate-fade-up"
                style={{ animationDelay: `${i * 0.1}s` }}
              >
                <div className="absolute -top-8 -right-8 w-20 h-20 rounded-full opacity-5 group-hover:opacity-10 transition-opacity"
                  style={{ backgroundImage: `linear-gradient(to bottom right, ${feature.from}, ${feature.to})` }}
                />
                <span className="text-3xl mb-4 block">{feature.icon}</span>
                <h3 className="font-display text-lg font-bold mb-2">{feature.title}</h3>
                <p className="text-sm text-[rgb(var(--color-text-secondary))] leading-relaxed">
                  {feature.desc}
                </p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Testimonial */}
      <section className="py-20 px-6 bg-[rgb(var(--color-surface))] border-y border-[rgb(var(--color-border))]">
        <div className="max-w-4xl mx-auto text-center">
          <div className="w-16 h-16 mx-auto mb-6 rounded-full bg-gradient-to-br from-[rgb(var(--color-accent))] to-[rgb(var(--color-navy-700))] flex items-center justify-center text-white text-2xl font-display font-bold">
            س
          </div>
          <blockquote className="font-display text-2xl md:text-3xl font-bold leading-relaxed mb-6">
            &ldquo;منذ استخدام DzCommerce، تضاعفت مبيعاتنا وأصبحت إدارة المخزون أسهل بكثير.&rdquo;
          </blockquote>
          <div>
            <p className="font-display font-bold">سارة أحمد</p>
            <p className="text-sm text-[rgb(var(--color-text-secondary))]">صاحبة متجر أزياء أونلاين</p>
          </div>
        </div>
      </section>

      {/* CTA */}
      <section className="py-24 px-6">
        <div className="max-w-3xl mx-auto text-center">
          <h2 className="font-display text-3xl md:text-4xl font-extrabold mb-4">ابدأ الآن مجانًا</h2>
          <p className="text-[rgb(var(--color-text-secondary))] text-lg mb-8">
            انضم إلى أكثر من ١٠٠ تاجر جزائري يديرون متاجرهم عبر DzCommerce
          </p>
          <Link href="/register">
            <Button size="lg">ابدأ النسخة التجريبية المجانية</Button>
          </Link>
        </div>
      </section>

      {/* Footer */}
      <footer className="border-t border-[rgb(var(--color-border))] py-10 px-6 bg-[rgb(var(--color-surface))]">
        <div className="max-w-6xl mx-auto">
          <div className="grid md:grid-cols-4 gap-8 mb-8">
            <div>
              <Link href="/" className="font-display text-lg font-extrabold tracking-tight">
                Dz<span className="text-[rgb(var(--color-accent))]">Commerce</span>
              </Link>
              <p className="text-sm text-[rgb(var(--color-text-secondary))] mt-2 leading-relaxed">
                منصة متكاملة لإدارة المتاجر الإلكترونية في الجزائر
              </p>
            </div>
            {[
              { title: "المنتج", links: ["المميزات", "التسعير", " API"] },
              { title: "الدعم", links: ["المساعدة", "التوثيق", "المدونة"] },
              { title: "الشركة", links: ["من نحن", "اتصل بنا", "الخصوصية"] },
            ].map((col) => (
              <div key={col.title}>
                <h4 className="font-display font-bold text-sm mb-3">{col.title}</h4>
                <ul className="space-y-2">
                  {col.links.map((link) => (
                    <li key={link}>
                      <Link href="#" className="text-sm text-[rgb(var(--color-text-secondary))] hover:text-[rgb(var(--color-text))] transition-colors">
                        {link}
                      </Link>
                    </li>
                  ))}
                </ul>
              </div>
            ))}
          </div>
          <div className="border-t border-[rgb(var(--color-border))] pt-8 flex flex-col md:flex-row items-center justify-between gap-4 text-sm text-[rgb(var(--color-text-secondary))]">
            <span>© {new Date().getFullYear()} DzCommerce — {t("footer_copyright")}</span>
            <span>{t("footer_made_in")}</span>
          </div>
        </div>
      </footer>
    </div>
  );
}
