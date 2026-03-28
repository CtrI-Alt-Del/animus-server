"""create analyses table

Revision ID: 20260328_110000
Revises: 20260327_120000
Create Date: 2026-03-28 11:00:00
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = '20260328_110000'
down_revision: str | None = '20260327_120000'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        'analyses',
        sa.Column('id', sa.String(length=26), nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('folder_id', sa.String(length=26), nullable=True),
        sa.Column('account_id', sa.String(length=26), nullable=False),
        sa.Column('status', sa.String(), nullable=False),
        sa.Column('is_archived', sa.Boolean(), nullable=False),
        sa.Column('summary', sa.Text(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_analyses_account_id'), 'analyses', ['account_id'])


def downgrade() -> None:
    op.drop_index(op.f('ix_analyses_account_id'), table_name='analyses')
    op.drop_table('analyses')
