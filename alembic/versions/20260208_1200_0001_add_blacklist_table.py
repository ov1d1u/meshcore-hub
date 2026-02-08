"""add blacklist table

Revision ID: 20260208_1200_0001
Revises: 4e2e787a1660
Create Date: 2026-02-08 12:00:00.000000+00:00

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "20260208_1200_0001"
down_revision: Union[str, None] = "4e2e787a1660"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "blacklist",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("public_key", sa.String(64), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("public_key"),
    )
    op.create_index("ix_blacklist_public_key", "blacklist", ["public_key"])


def downgrade() -> None:
    op.drop_index("ix_blacklist_public_key", table_name="blacklist")
    op.drop_table("blacklist")
