"""add petitions analysis fk cascade

Revision ID: 20260404_120000
Revises: 20260404_110000
Create Date: 2026-04-04 12:00:00
"""

from collections.abc import Sequence

from alembic import op


# revision identifiers, used by Alembic.
revision: str = '20260404_120000'
down_revision: str | None = '20260404_110000'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute(
        'ALTER TABLE petitions '
        'DROP CONSTRAINT IF EXISTS petitions_analysis_id_fkey'
    )
    op.execute(
        'ALTER TABLE petitions '
        'ADD CONSTRAINT petitions_analysis_id_fkey '
        'FOREIGN KEY (analysis_id) REFERENCES analyses (id) ON DELETE CASCADE'
    )


def downgrade() -> None:
    op.execute(
        'ALTER TABLE petitions '
        'DROP CONSTRAINT IF EXISTS petitions_analysis_id_fkey'
    )
