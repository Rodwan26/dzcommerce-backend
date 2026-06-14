# MVP Roadmap — DzCommerce

## 🎯 الهدف
SaaS B2B جزائري ERP-lite + E-commerce
للشركات الصغيرة والمتوسطة في الجزائر.

---

## 📅 الجدول الزمني (3 أشهر)

### 🟢 الشهر 1 — Auth + Tenant + Approval

| الأسبوع | المهمة | المخرجات |
|---------|--------|----------|
| 1-2 | Database schema + Alembic + Config | 11 جدول، اتصال Postgres، متغيرات البيئة |
| 2-3 | Auth system | Register → Verify → Login → JWT (access + refresh) |
| 3-4 | Tenant system | Instant trial، طلب approval، dashboard admin |

### 🟡 الشهر 2 — Products + Orders + COD

| الأسبوع | المهمة | المخرجات |
|---------|--------|----------|
| 5 | Products CRUD + Categories | API كامل للمنتجات مع tenant isolation |
| 6 | Orders + State Machine | pending → confirmed → shipped → delivered → returned |
| 7 | COD Payments | إنشاء دفعة، تحصيل، tracking |
| 8 | Tenant Middleware + Audit + Features | Security-grade middleware، audit logs، feature flags |

### 🔵 الشهر 3 — Dashboard + Export + Integration

| الأسبوع | المهمة | المخرجات |
|---------|--------|----------|
| 9 | Dashboard endpoints | إحصائيات المبيعات، المنتجات، الطلبات |
| 10 | Excel Export + WhatsApp | تصدير XLSX، إشعارات واتساب |
| 11 | Testing | Unit + Integration tests |
| 12 | Docker + Deploy | Docker Compose، نشر على VPS |

---

## 🏗️ Tech Stack

| الطبقة | التقنية |
|--------|---------|
| Backend | Python FastAPI |
| Database | PostgreSQL 16 |
| ORM | SQLAlchemy 2.0 (async) |
| Migrations | Alembic |
| Auth | JWT (access + refresh) |
| Cache | Redis |
| Container | Docker + Docker Compose |

---

## 📊 MVP Features

### ✅ Must-have (الشهر 1-2)
- [x] Multi-tenant architecture
- [x] Admin approval system
- [x] COD payments
- [x] Order state machine
- [x] Audit logs
- [x] Feature flags

### ✅ Nice-to-have (الشهر 3)
- [ ] WhatsApp notifications
- [ ] Excel export
- [ ] Analytics dashboard
- [ ] SMS integration
