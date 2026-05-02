"""create analysies precedent legal features table

Revision ID: 20260425_180000
Revises: 20260423_010000
Create Date: 2026-04-25 18:00:00
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '20260425_180000'
down_revision: str | None = '20260423_010000'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        'analysies_precedent_legal_features',
        sa.Column('analysis_id', sa.String(length=26), nullable=False),
        sa.Column('precedent_id', sa.String(length=26), nullable=False),
        sa.Column('same_law_count', sa.Integer(), nullable=False),
        sa.Column('same_decree_count', sa.Integer(), nullable=False),
        sa.Column('type_of_action_match', sa.Integer(), nullable=False),
        sa.Column('requested_relief_overlap_count', sa.Integer(), nullable=False),
        sa.Column('has_regime_mismatch', sa.Integer(), nullable=False),
        sa.Column('has_specialization_mismatch', sa.Integer(), nullable=False),
        sa.Column('has_accessory_topic_overlap', sa.Integer(), nullable=False),
        sa.Column('jurisdiction_match', sa.Integer(), nullable=False),
        sa.Column('standing_match', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(
            ['analysis_id', 'precedent_id'],
            ['analysis_precedents.analysis_id', 'analysis_precedents.precedent_id'],
            ondelete='CASCADE',
        ),
        sa.PrimaryKeyConstraint('analysis_id', 'precedent_id'),
    )


def downgrade() -> None:
    op.drop_table('analysies_precedent_legal_features')
