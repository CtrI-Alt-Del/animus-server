"""create analysis precedents table

Revision ID: 20260328_150000
Revises: ee4204a91fe4
Create Date: 2026-03-28 15:00:00
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = '20260328_150000'
down_revision: str | None = 'ee4204a91fe4'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        'analysis_precedents',
        sa.Column('analysis_id', sa.String(length=26), nullable=False),
        sa.Column('precedent_id', sa.String(length=26), nullable=False),
        sa.Column('is_chosen', sa.Boolean(), nullable=False),
        sa.Column('applicability_percentage', sa.Float(), nullable=True),
        sa.Column('synthesis', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['analysis_id'], ['analyses.id']),
        sa.ForeignKeyConstraint(['precedent_id'], ['precedents.id']),
        sa.PrimaryKeyConstraint('analysis_id', 'precedent_id'),
    )


def downgrade() -> None:
    op.drop_table('analysis_precedents')
