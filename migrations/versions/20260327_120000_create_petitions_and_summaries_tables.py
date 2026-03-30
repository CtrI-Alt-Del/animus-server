"""create petitions and petition summaries tables

Revision ID: 20260327_120000
Revises: 8cb87a9d6608
Create Date: 2026-03-27 12:00:00
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = '20260327_120000'
down_revision: str | None = '8cb87a9d6608'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        'petitions',
        sa.Column('id', sa.String(length=26), nullable=False),
        sa.Column('analysis_id', sa.String(length=26), nullable=False),
        sa.Column('uploaded_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('document_file_path', sa.String(), nullable=False),
        sa.Column('document_name', sa.String(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_petitions_analysis_id'), 'petitions', ['analysis_id'])

    op.create_table(
        'petition_summaries',
        sa.Column('petition_id', sa.String(length=26), nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('main_points', sa.JSON(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['petition_id'], ['petitions.id']),
        sa.PrimaryKeyConstraint('petition_id'),
    )


def downgrade() -> None:
    op.drop_table('petition_summaries')
    op.drop_index(op.f('ix_petitions_analysis_id'), table_name='petitions')
    op.drop_table('petitions')
