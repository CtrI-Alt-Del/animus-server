"""add analysis precedent scores columns

Revision ID: 20260418_130000
Revises: 20260418_120000
Create Date: 2026-04-18 13:00:00
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '20260418_130000'
down_revision: str | None = '20260418_120000'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        'analysis_precedents',
        sa.Column(
            'thesis_similarity_score', sa.Float(), nullable=False, server_default='0'
        ),
    )
    op.add_column(
        'analysis_precedents',
        sa.Column(
            'enunciation_similarity_score',
            sa.Float(),
            nullable=False,
            server_default='0',
        ),
    )
    op.add_column(
        'analysis_precedents',
        sa.Column(
            'total_search_hits', sa.Integer(), nullable=False, server_default='0'
        ),
    )
    op.add_column(
        'analysis_precedents',
        sa.Column('similarity_rank', sa.Integer(), nullable=False, server_default='0'),
    )
    op.add_column(
        'analysis_precedents',
        sa.Column(
            'applicability_level', sa.Integer(), nullable=False, server_default='0'
        ),
    )

    op.execute(
        sa.text(
            """
            UPDATE analysis_precedents
            SET applicability_level =
                CASE
                    WHEN similarity_score IS NULL THEN 0
                    WHEN similarity_score >= 85 THEN 2
                    WHEN similarity_score >= 70 THEN 1
                    ELSE 0
                END
            """
        )
    )

    op.alter_column(
        'analysis_precedents', 'thesis_similarity_score', server_default=None
    )
    op.alter_column(
        'analysis_precedents',
        'enunciation_similarity_score',
        server_default=None,
    )
    op.alter_column('analysis_precedents', 'total_search_hits', server_default=None)
    op.alter_column('analysis_precedents', 'similarity_rank', server_default=None)
    op.alter_column('analysis_precedents', 'applicability_level', server_default=None)


def downgrade() -> None:
    op.drop_column('analysis_precedents', 'applicability_level')
    op.drop_column('analysis_precedents', 'similarity_rank')
    op.drop_column('analysis_precedents', 'total_search_hits')
    op.drop_column('analysis_precedents', 'enunciation_similarity_score')
    op.drop_column('analysis_precedents', 'thesis_similarity_score')
