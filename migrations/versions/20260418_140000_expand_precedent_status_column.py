"""expand precedent status column length

Revision ID: 20260418_140000
Revises: 20260418_130000
Create Date: 2026-04-18 14:00:00
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '20260418_140000'
down_revision: str | None = '20260418_130000'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.alter_column(
        'precedents',
        'status',
        existing_type=sa.String(length=50),
        type_=sa.String(length=120),
        existing_nullable=False,
    )


def downgrade() -> None:
    op.alter_column(
        'precedents',
        'status',
        existing_type=sa.String(length=120),
        type_=sa.String(length=50),
        existing_nullable=False,
    )
