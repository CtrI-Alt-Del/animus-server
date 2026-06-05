"""create second instance decisions

Revision ID: 20260604_160000
Revises: 20260604_150000
Create Date: 2026-06-04 16:00:00
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '20260604_160000'
down_revision: str | Sequence[str] | None = '20260604_150000'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        'second_instance_decisions',
        sa.Column('analysis_id', sa.String(length=26), nullable=False),
        sa.Column('description', sa.Text(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['analysis_id'], ['analyses.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('analysis_id'),
    )


def downgrade() -> None:
    op.drop_table('second_instance_decisions')
