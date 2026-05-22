"""rename judgment drafts table

Revision ID: 20260516_143500
Revises: 20260514_120000
Create Date: 2026-05-16 14:35:00
"""

from collections.abc import Sequence

from alembic import op


# revision identifiers, used by Alembic.
revision: str = '20260516_143500'
down_revision: str | Sequence[str] | None = '20260514_120000'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.rename_table('judgment_drafts', 'second_instance_judgment_drafts')


def downgrade() -> None:
    op.rename_table('second_instance_judgment_drafts', 'judgment_drafts')
