"""add buyer_profiles

Revision ID: a1b2c3d4e5f6
Revises: d2f8a4c15e91
Create Date: 2026-07-06 00:00:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa
import sqlmodel  # SQLModel column types (e.g. AutoString) appear in migrations
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "a1b2c3d4e5f6"
down_revision: str | Sequence[str] | None = "d2f8a4c15e91"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        "buyer_profiles",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("uuid", sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("tenant_id", sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column("phone", sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column("name", sqlmodel.sql.sqltypes.AutoString(), nullable=True),
        sa.Column("budget", sqlmodel.sql.sqltypes.AutoString(), nullable=True),
        sa.Column("area", sqlmodel.sql.sqltypes.AutoString(), nullable=True),
        sa.Column("prefs_summary", sqlmodel.sql.sqltypes.AutoString(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "tenant_id", "phone", name="uq_buyer_profiles_tenant_phone"
        ),
    )
    op.create_index(
        op.f("ix_buyer_profiles_phone"), "buyer_profiles", ["phone"], unique=False
    )
    op.create_index(
        op.f("ix_buyer_profiles_tenant_id"),
        "buyer_profiles",
        ["tenant_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_buyer_profiles_uuid"), "buyer_profiles", ["uuid"], unique=True
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index(op.f("ix_buyer_profiles_uuid"), table_name="buyer_profiles")
    op.drop_index(op.f("ix_buyer_profiles_tenant_id"), table_name="buyer_profiles")
    op.drop_index(op.f("ix_buyer_profiles_phone"), table_name="buyer_profiles")
    op.drop_table("buyer_profiles")
