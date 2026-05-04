"""create folders table

Revision ID: 20260420_120001
Revises: 20260418_140000, 2ee630b3a47c
Create Date: 2026-04-20 12:00:00
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '20260420_120001'
down_revision: str | Sequence[str] | None = ('20260418_140000', '2ee630b3a47c')
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        'folders',
        sa.Column('id', sa.String(length=26), nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('account_id', sa.String(length=26), nullable=False),
        sa.Column('is_archived', sa.Boolean(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_folders_account_id'), 'folders', ['account_id'])
    op.create_index(op.f('ix_analyses_folder_id'), 'analyses', ['folder_id'])


def downgrade() -> None:
    op.drop_index(op.f('ix_analyses_folder_id'), table_name='analyses')
    op.drop_index(op.f('ix_folders_account_id'), table_name='folders')
    op.drop_table('folders')
