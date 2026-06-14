import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, generate_uuid


class Tenant(Base, TimestampMixin):
    __tablename__ = "tenants"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=generate_uuid)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    slug: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="active")
    trial_ends_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    google_sheet_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    google_sheet_enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    google_sheet_last_sync_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    facebook_access_token: Mapped[str | None] = mapped_column(String(512), nullable=True)
    facebook_ad_account_id: Mapped[str | None] = mapped_column(String(100), nullable=True)
    facebook_sync_enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    facebook_last_sync_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    facebook_last_test_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    facebook_last_test_success: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    facebook_last_error: Mapped[str | None] = mapped_column(Text, nullable=True)
    google_last_test_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    google_last_test_success: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    google_last_error: Mapped[str | None] = mapped_column(Text, nullable=True)

    users = relationship("User", back_populates="tenant", lazy="selectin")
    settings = relationship("TenantSettings", back_populates="tenant", uselist=False, lazy="selectin")
    features = relationship("TenantFeature", back_populates="tenant", lazy="selectin")
    subscription = relationship("Subscription", back_populates="tenant", uselist=False, lazy="selectin")
    products = relationship("Product", back_populates="tenant", lazy="selectin")
    orders = relationship("Order", back_populates="tenant", lazy="selectin")
    payments = relationship("Payment", back_populates="tenant", lazy="selectin")
    audit_logs = relationship("AuditLog", back_populates="tenant", lazy="selectin")
