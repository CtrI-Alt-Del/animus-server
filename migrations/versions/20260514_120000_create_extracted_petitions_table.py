"""create extracted petitions table

Revision ID: 20260514_120000
Revises: 20260511_120000
Create Date: 2026-05-14 12:00:00
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = '20260514_120000'
down_revision: str | None = '20260511_120000'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        'extracted_petitions',
        sa.Column('analysis_id', sa.String(length=26), nullable=False),
        sa.Column('first_page', sa.Integer(), nullable=False),
        sa.Column('last_page', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['analysis_id'], ['analyses.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('analysis_id'),
    )


def downgrade() -> None:
    op.drop_table('extracted_petitions')
