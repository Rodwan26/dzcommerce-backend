"""add facebook ads fields to tenants + facebook_campaign_metrics

Revision ID: 005
Revises: 004
Create Date: 2026-06-13

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID


revision: str = "005"
down_revision: Union[str, None] = "004"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("tenants", sa.Column("facebook_access_token", sa.String(512), nullable=True))
    op.add_column("tenants", sa.Column("facebook_ad_account_id", sa.String(100), nullable=True))
    op.add_column("tenants", sa.Column("facebook_sync_enabled", sa.Boolean(), nullable=False, server_default=sa.text("false")))
    op.add_column("tenants", sa.Column("facebook_last_sync_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("tenants", sa.Column("facebook_last_error", sa.Text(), nullable=True))

    op.create_table(
        "facebook_campaign_metrics",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("tenant_id", UUID(as_uuid=True), nullable=False, index=True),
        sa.Column("campaign_id", sa.String(50), nullable=False),
        sa.Column("campaign_name", sa.String(255), nullable=False),
        sa.Column("campaign_status", sa.String(20), nullable=False),
        sa.Column("date", sa.Date(), nullable=False),
        sa.Column("spend", sa.Numeric(12, 2), nullable=False, server_default=sa.text("0")),
        sa.Column("currency", sa.String(10), nullable=True),
        sa.Column("impressions", sa.BigInteger(), nullable=False, server_default=sa.text("0")),
        sa.Column("clicks", sa.BigInteger(), nullable=False, server_default=sa.text("0")),
        sa.Column("ctr", sa.Float(), nullable=False, server_default=sa.text("0")),
        sa.Column("cpc", sa.Numeric(10, 4), nullable=False, server_default=sa.text("0")),
        sa.Column("cpm", sa.Numeric(10, 4), nullable=False, server_default=sa.text("0")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.UniqueConstraint("tenant_id", "campaign_id", "date", name="uq_facebook_campaign_metric"),
    )


def downgrade() -> None:
    op.drop_table("facebook_campaign_metrics")
    op.drop_column("tenants", "facebook_last_error")
    op.drop_column("tenants", "facebook_last_sync_at")
    op.drop_column("tenants", "facebook_sync_enabled")
    op.drop_column("tenants", "facebook_ad_account_id")
    op.drop_column("tenants", "facebook_access_token")
