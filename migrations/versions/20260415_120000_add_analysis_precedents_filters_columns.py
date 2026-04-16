"""add analysis precedents filters columns

Revision ID: 20260415_120000
Revises: 20260404_120000
Create Date: 2026-04-15 12:00:00
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '20260415_120000'
down_revision: str | None = '20260404_120000'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        'analyses',
        sa.Column('precedents_search_courts', sa.JSON(), nullable=True),
    )
    op.add_column(
        'analyses',
        sa.Column('precedents_search_precedent_kinds', sa.JSON(), nullable=True),
    )
    op.add_column(
        'analyses',
        sa.Column('precedents_search_limit', sa.Integer(), nullable=True),
    )

    op.execute(
        sa.text(
            """
            UPDATE analyses
            SET
                precedents_search_courts = '[]'::json,
                precedents_search_precedent_kinds = '[]'::json,
                precedents_search_limit = 10
            """
        )
    )


def downgrade() -> None:
    op.drop_column('analyses', 'precedents_search_limit')
    op.drop_column('analyses', 'precedents_search_precedent_kinds')
    op.drop_column('analyses', 'precedents_search_courts')
