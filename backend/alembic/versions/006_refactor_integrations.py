"""refactor integrations: provider credentials, last_test fields

Revision ID: 006
Revises: 005
Create Date: 2026-06-13

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSON


revision: str = "006"
down_revision: Union[str, None] = "005"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Tenant — google test fields
    op.add_column("tenants", sa.Column("google_last_test_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("tenants", sa.Column("google_last_test_success", sa.Boolean(), nullable=True))
    op.add_column("tenants", sa.Column("google_last_error", sa.Text(), nullable=True))

    # Tenant — facebook test fields
    op.add_column("tenants", sa.Column("facebook_last_test_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("tenants", sa.Column("facebook_last_test_success", sa.Boolean(), nullable=True))

    # ShippingProvider — add new columns
    op.add_column("shipping_providers", sa.Column("provider_type", sa.String(50), nullable=False, server_default="custom"))
    op.add_column("shipping_providers", sa.Column("credentials", JSON, nullable=True))
    op.add_column("shipping_providers", sa.Column("last_test_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("shipping_providers", sa.Column("last_test_success", sa.Boolean(), nullable=True))
    op.add_column("shipping_providers", sa.Column("last_error", sa.Text(), nullable=True))

    # ShippingProvider — migrate existing api_key into credentials
    conn = op.get_bind()
    conn.execute(
        sa.text(
            "UPDATE shipping_providers SET credentials = jsonb_build_object('api_key', api_key) WHERE api_key IS NOT NULL AND api_key != ''"
        )
    )

    # ShippingProvider — drop old columns
    op.drop_column("shipping_providers", "api_url")
    op.drop_column("shipping_providers", "api_key")


def downgrade() -> None:
    # ShippingProvider — restore old columns
    op.add_column("shipping_providers", sa.Column("api_key", sa.String(500), nullable=False, server_default=""))
    op.add_column("shipping_providers", sa.Column("api_url", sa.String(500), nullable=False, server_default=""))

    # ShippingProvider — migrate credentials back
    conn = op.get_bind()
    conn.execute(
        sa.text(
            "UPDATE shipping_providers SET api_key = credentials->>'api_key' WHERE credentials IS NOT NULL"
        )
    )

    op.drop_column("shipping_providers", "last_error")
    op.drop_column("shipping_providers", "last_test_success")
    op.drop_column("shipping_providers", "last_test_at")
    op.drop_column("shipping_providers", "credentials")
    op.drop_column("shipping_providers", "provider_type")

    # Tenant — drop facebook test fields
    op.drop_column("tenants", "facebook_last_test_success")
    op.drop_column("tenants", "facebook_last_test_at")

    # Tenant — drop google test fields
    op.drop_column("tenants", "google_last_error")
    op.drop_column("tenants", "google_last_test_success")
    op.drop_column("tenants", "google_last_test_at")
