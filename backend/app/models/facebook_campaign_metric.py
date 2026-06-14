import uuid
from datetime import date, datetime

from sqlalchemy import BigInteger, Date, Float, Numeric, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, generate_uuid


class FacebookCampaignMetric(Base, TimestampMixin):
    __tablename__ = "facebook_campaign_metrics"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=generate_uuid)
    tenant_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), index=True, nullable=False
    )
    campaign_id: Mapped[str] = mapped_column(String(50), nullable=False)
    campaign_name: Mapped[str] = mapped_column(String(255), nullable=False)
    campaign_status: Mapped[str] = mapped_column(String(20), nullable=False)
    date: Mapped[date] = mapped_column(Date, nullable=False)
    spend: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False, default=0)
    currency: Mapped[str | None] = mapped_column(String(10), nullable=True)
    impressions: Mapped[int] = mapped_column(BigInteger, nullable=False, default=0)
    clicks: Mapped[int] = mapped_column(BigInteger, nullable=False, default=0)
    ctr: Mapped[float] = mapped_column(Float, nullable=False, default=0)
    cpc: Mapped[float] = mapped_column(Numeric(10, 4), nullable=False, default=0)
    cpm: Mapped[float] = mapped_column(Numeric(10, 4), nullable=False, default=0)

    __table_args__ = (
        UniqueConstraint("tenant_id", "campaign_id", "date", name="uq_facebook_campaign_metric"),
    )
