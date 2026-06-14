"""add confirmation_status, shipping_status, confirmed_at, order_status_history

Revision ID: 003
Revises: 002
Create Date: 2026-06-13

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID

revision: str = "003"
down_revision: Union[str, None] = "002"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add new columns to orders (status stays as deprecated)
    op.add_column("orders", sa.Column("confirmation_status", sa.String(20), nullable=False, server_default="pending"))
    op.add_column("orders", sa.Column("shipping_status", sa.String(20), nullable=False, server_default="not_sent"))
    op.add_column("orders", sa.Column("confirmed_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("orders", sa.Column("updated_source", sa.String(20), nullable=True))
    op.add_column("orders", sa.Column("updated_by_user_id", UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True))
    op.add_column("orders", sa.Column("updated_source_ref", sa.String(255), nullable=True))

    # Backfill data from legacy status column
    conn = op.get_bind()
    conn.execute(
        sa.text("""
            UPDATE orders
            SET
                confirmation_status = CASE
                    WHEN status = 'pending' THEN 'pending'
                    WHEN status = 'confirmed' THEN 'confirmed'
                    WHEN status = 'shipped' THEN 'confirmed'
                    WHEN status = 'delivered' THEN 'confirmed'
                    WHEN status = 'returned' THEN 'confirmed'
                    WHEN status = 'cancelled' THEN 'cancelled'
                    ELSE 'pending'
                END,
                shipping_status = CASE
                    WHEN status = 'pending' THEN 'not_sent'
                    WHEN status = 'confirmed' THEN 'not_sent'
                    WHEN status = 'shipped' THEN 'in_transit'
                    WHEN status = 'delivered' THEN 'delivered'
                    WHEN status = 'returned' THEN 'returned'
                    WHEN status = 'cancelled' THEN 'not_sent'
                    ELSE 'not_sent'
                END,
                confirmed_at = CASE
                    WHEN status IN ('confirmed', 'shipped', 'delivered', 'returned') THEN created_at
                    ELSE NULL
                END
        """)
    )

    # Create order_status_history table
    op.create_table(
        "order_status_history",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("order_id", UUID(as_uuid=True), sa.ForeignKey("orders.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("shipment_id", UUID(as_uuid=True), sa.ForeignKey("shipments.id", ondelete="SET NULL"), nullable=True, index=True),
        sa.Column("field_name", sa.String(30), nullable=False),
        sa.Column("old_value", sa.String(20), nullable=True),
        sa.Column("new_value", sa.String(20), nullable=True),
        sa.Column("source", sa.String(20), nullable=False),
        sa.Column("source_ref", sa.String(255), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), index=True),
    )


def downgrade() -> None:
    op.drop_table("order_status_history")
    op.drop_column("orders", "updated_source_ref")
    op.drop_column("orders", "updated_by_user_id")
    op.drop_column("orders", "updated_source")
    op.drop_column("orders", "confirmed_at")
    op.drop_column("orders", "shipping_status")
    op.drop_column("orders", "confirmation_status")
