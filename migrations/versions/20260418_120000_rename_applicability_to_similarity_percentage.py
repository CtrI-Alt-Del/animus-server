"""rename applicability_percentage to similarity_score

Revision ID: 20260418_120000
Revises: 20260415_120000
Create Date: 2026-04-18 12:00:00
"""

from collections.abc import Sequence

from alembic import op


# revision identifiers, used by Alembic.
revision: str = '20260418_120000'
down_revision: str | None = '20260415_120000'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.alter_column(
        'analysis_precedents',
        'applicability_percentage',
        new_column_name='similarity_score',
    )


def downgrade() -> None:
    op.alter_column(
        'analysis_precedents',
        'similarity_score',
        new_column_name='applicability_percentage',
    )
