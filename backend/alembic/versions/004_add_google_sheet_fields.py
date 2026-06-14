"""add google_sheet fields to tenants

Revision ID: 004
Revises: 003
Create Date: 2026-06-13

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "004"
down_revision: Union[str, None] = "003"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("tenants", sa.Column("google_sheet_id", sa.String(255), nullable=True))
    op.add_column("tenants", sa.Column("google_sheet_enabled", sa.Boolean(), nullable=False, server_default=sa.text("false")))
    op.add_column("tenants", sa.Column("google_sheet_last_sync_at", sa.DateTime(timezone=True), nullable=True))


def downgrade() -> None:
    op.drop_column("tenants", "google_sheet_last_sync_at")
    op.drop_column("tenants", "google_sheet_enabled")
    op.drop_column("tenants", "google_sheet_id")
