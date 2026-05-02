"""add final_rank to analysis precedents

Revision ID: 20260426_160000
Revises: 20260426_130000
Create Date: 2026-04-26 16:00:00
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '20260426_160000'
down_revision: str | None = '20260426_130000'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        'analysis_precedents',
        sa.Column('final_rank', sa.Integer(), nullable=False, server_default='0'),
    )

    op.execute(sa.text('UPDATE analysis_precedents SET final_rank = similarity_rank'))

    op.alter_column('analysis_precedents', 'final_rank', server_default=None)


def downgrade() -> None:
    op.drop_column('analysis_precedents', 'final_rank')
