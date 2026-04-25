"""create analysis precedent feedback tables

Revision ID: 20260420_120000
Revises: 20260418_140000
Create Date: 2026-04-20 12:00:00
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '20260420_120000'
down_revision: str | None = '20260418_140000'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        'analysis_precedent_applicability_feedbacks',
        sa.Column('analysis_id', sa.String(length=26), nullable=False),
        sa.Column('precedent_id', sa.String(length=26), nullable=False),
        sa.Column('applicability_level', sa.Integer(), nullable=False),
        sa.Column('is_from_human', sa.Boolean(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(
            ['analysis_id', 'precedent_id'],
            ['analysis_precedents.analysis_id', 'analysis_precedents.precedent_id'],
            ondelete='CASCADE',
        ),
        sa.PrimaryKeyConstraint('analysis_id', 'precedent_id'),
    )

    op.create_table(
        'analysis_precedent_dataset_rows',
        sa.Column('analysis_id', sa.String(length=26), nullable=False),
        sa.Column('precedent_id', sa.String(length=26), nullable=False),
        sa.Column('applicability_level', sa.Integer(), nullable=False),
        sa.Column('is_from_human', sa.Boolean(), nullable=False),
        sa.Column('thesis_similarity_score', sa.Float(), nullable=False),
        sa.Column('enunciation_similarity_score', sa.Float(), nullable=False),
        sa.Column('total_search_hits', sa.Integer(), nullable=False),
        sa.Column('similarity_rank', sa.Integer(), nullable=False),
        sa.Column('identifier_court', sa.String(length=10), nullable=False),
        sa.Column('identifier_kind', sa.String(length=10), nullable=False),
        sa.Column('identifier_number', sa.Integer(), nullable=False),
        sa.Column('precedent_status', sa.String(length=120), nullable=False),
        sa.Column('last_updated_in_pangea_at', sa.DateTime(timezone=True), nullable=False),
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
    op.drop_table('analysis_precedent_dataset_rows')
    op.drop_table('analysis_precedent_applicability_feedbacks')
