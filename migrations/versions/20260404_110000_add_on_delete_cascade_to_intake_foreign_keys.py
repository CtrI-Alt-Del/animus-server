"""add on delete cascade to intake foreign keys

Revision ID: 20260404_110000
Revises: 20260330_120000
Create Date: 2026-04-04 11:00:00
"""

from collections.abc import Sequence

from alembic import op


# revision identifiers, used by Alembic.
revision: str = '20260404_110000'
down_revision: str | None = '20260330_120000'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute(
        'ALTER TABLE petition_summaries '
        'DROP CONSTRAINT IF EXISTS petition_summaries_petition_id_fkey'
    )
    op.execute(
        'ALTER TABLE petition_summaries '
        'ADD CONSTRAINT petition_summaries_petition_id_fkey '
        'FOREIGN KEY (petition_id) REFERENCES petitions (id) ON DELETE CASCADE'
    )

    op.execute(
        'ALTER TABLE analysis_precedents '
        'DROP CONSTRAINT IF EXISTS analysis_precedents_analysis_id_fkey'
    )
    op.execute(
        'ALTER TABLE analysis_precedents '
        'ADD CONSTRAINT analysis_precedents_analysis_id_fkey '
        'FOREIGN KEY (analysis_id) REFERENCES analyses (id) ON DELETE CASCADE'
    )

    op.execute(
        'ALTER TABLE analysis_precedents '
        'DROP CONSTRAINT IF EXISTS analysis_precedents_precedent_id_fkey'
    )
    op.execute(
        'ALTER TABLE analysis_precedents '
        'ADD CONSTRAINT analysis_precedents_precedent_id_fkey '
        'FOREIGN KEY (precedent_id) REFERENCES precedents (id) ON DELETE CASCADE'
    )


def downgrade() -> None:
    op.execute(
        'ALTER TABLE petition_summaries '
        'DROP CONSTRAINT IF EXISTS petition_summaries_petition_id_fkey'
    )
    op.execute(
        'ALTER TABLE petition_summaries '
        'ADD CONSTRAINT petition_summaries_petition_id_fkey '
        'FOREIGN KEY (petition_id) REFERENCES petitions (id)'
    )

    op.execute(
        'ALTER TABLE analysis_precedents '
        'DROP CONSTRAINT IF EXISTS analysis_precedents_analysis_id_fkey'
    )
    op.execute(
        'ALTER TABLE analysis_precedents '
        'ADD CONSTRAINT analysis_precedents_analysis_id_fkey '
        'FOREIGN KEY (analysis_id) REFERENCES analyses (id)'
    )

    op.execute(
        'ALTER TABLE analysis_precedents '
        'DROP CONSTRAINT IF EXISTS analysis_precedents_precedent_id_fkey'
    )
    op.execute(
        'ALTER TABLE analysis_precedents '
        'ADD CONSTRAINT analysis_precedents_precedent_id_fkey '
        'FOREIGN KEY (precedent_id) REFERENCES precedents (id)'
    )
