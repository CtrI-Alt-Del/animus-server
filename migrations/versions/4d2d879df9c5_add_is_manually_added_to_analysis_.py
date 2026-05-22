"""add is_manually_added to analysis precedents

Revision ID: 4d2d879df9c5
Revises: 20260517_223000
Create Date: 2026-05-20 15:54:52.341692
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '4d2d879df9c5'
down_revision: str | Sequence[str] | None = '20260517_223000'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        'analysis_precedents',
        sa.Column(
            'is_manually_added',
            sa.Boolean(),
            nullable=False,
            server_default=sa.text('false'),
        ),
    )
    op.alter_column('analysis_precedents', 'is_manually_added', server_default=None)


def downgrade() -> None:
    op.drop_column('analysis_precedents', 'is_manually_added')
